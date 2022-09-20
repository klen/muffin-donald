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


@tasks.task
async def task1():
    logger.info("Task1: done")
    return 42


@tasks.schedule(2e-1)
@tasks.task
async def ping():
    with open(Path(__file__).parent / "ping", "w") as f:
        f.write("PONG")
    logger.info("Ping: done")


def test_base():
    assert "tasks_worker" in app.manage.commands
    assert "tasks_scheduler" in app.manage.commands


async def test_start(caplog):
    assert tasks
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
