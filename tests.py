import muffin
import asyncio
import pytest
from asgi_tools.tests import manage_lifespan


@pytest.fixture
def aiolib():
    return ('asyncio', {'use_uvloop': False})


@pytest.fixture
def app():
    return muffin.Application(DEBUG=True)


async def task1():
    return 42


async def ping():
    print("PONG")


async def test_base(app, capsys):
    from muffin_donald import Plugin

    tasks = Plugin(app, autostart=True, num_workers=2)
    assert tasks
    assert tasks.donald

    tasks.schedule(2e-1)(ping)

    async with manage_lifespan(app):
        assert tasks.donald._started
        assert tasks.donald.schedules
        assert len(tasks.donald.workers) == 2
        res = await tasks.submit(task1)
        assert res == 42
        await asyncio.sleep(.2)

    captured = capsys.readouterr()
    assert "Next 'ping'" in captured.err

    assert not tasks.donald._started
