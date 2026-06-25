import asyncio

from asgi_tools.tests import manage_lifespan

from .conftest import PROJECT_ROOT, app, fail_task, task1, tasks


async def test_start(caplog):
    assert tasks.manager

    async with manage_lifespan(app):
        assert tasks.manager.ready.is_set()
        assert tasks.manager._backend.is_connected
        assert tasks.manager.scheduler._tasks

        await task1.submit()
        await asyncio.sleep(3e-1)

    assert PROJECT_ROOT.joinpath("ping").read_text() == "PONG"

    assert not tasks.manager.ready.is_set()
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
