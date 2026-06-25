import asyncio

from asgi_tools.tests import manage_lifespan

from .conftest import app, immediate_task


def test_immediate_schedule(caplog):
    immediate_task.schedule(1e-1, run_immediately=True)

    async def runner():
        async with manage_lifespan(app):
            await asyncio.sleep(0.2)

    asyncio.run(runner())
    log_messages = [r.message for r in caplog.records]
    assert "Immediate task ran" in log_messages
