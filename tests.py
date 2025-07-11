import asyncio
from pathlib import Path

import muffin
import pytest
from asgi_tools.tests import manage_lifespan

from muffin_donald import Plugin, logger


@pytest.fixture
def aiolib():
    return ("asyncio", {"use_uvloop": False})


app = muffin.Application(DEBUG=True)
tasks = Plugin(app, start_worker=True, start_scheduler=True)


@tasks.task()
async def task1():
    logger.info("Task1: done")
    return 42


@tasks.task()
async def fail_task():
    raise ValueError("expected failure")


@tasks.task()
async def ping():
    with open(Path(__file__).parent / "ping", "w") as f:
        f.write("PONG")
    logger.info("Ping: done")


ping.schedule(2e-1)


def test_plugin_setup_defaults():
    plugin = Plugin(app, backend="memory", start_worker=True)
    assert plugin.cfg.backend == "memory"
    assert plugin.cfg.start_worker is True


def test_base():
    assert "tasks-worker" in app.manage.commands
    assert "tasks-scheduler" in app.manage.commands
    assert "tasks-healthcheck" in app.manage.commands


async def test_start(caplog):
    assert tasks.manager

    async with manage_lifespan(app):
        assert tasks.manager.is_started
        assert tasks.manager._backend.is_connected
        assert tasks.manager.scheduler._tasks

        await task1.submit()
        await asyncio.sleep(3e-1)

    with open(Path(__file__).parent / "ping", "r") as f:
        assert f.read() == "PONG"

    assert not tasks.manager.is_started
    log_messages = [r.message for r in caplog.records]
    assert "Task1: done" in log_messages
    assert "Ping: done" in log_messages


async def test_submit_and_wait():
    async with manage_lifespan(app):
        result = await task1.submit_and_wait()
        assert result == 42


async def test_on_error():
    errors = []

    @tasks.on_error
    async def handle_error(exc):
        errors.append(str(exc))

    async with manage_lifespan(app):
        await fail_task.submit()
        await asyncio.sleep(0.1)

    assert any("expected failure" in e for e in errors)


async def test_shutdown_cleanup():
    async with manage_lifespan(app):
        assert tasks.worker is not None
    assert not tasks.manager.is_started
    assert tasks.worker is None or not tasks.worker._tasks


@tasks.task()
async def immediate_task():
    logger.info("Immediate task ran")


def test_immediate_schedule(caplog):
    immediate_task.schedule(1e-1, run_immediately=True)

    async def runner():
        async with manage_lifespan(app):
            await asyncio.sleep(0.2)

    asyncio.run(runner())
    log_messages = [r.message for r in caplog.records]
    assert "Immediate task ran" in log_messages


async def test_healthcheck():
    healthcheck = app.manage.commands["tasks-healthcheck"]

    with pytest.raises(SystemExit):
        assert await healthcheck()

    async with manage_lifespan(app):
        assert await healthcheck()
