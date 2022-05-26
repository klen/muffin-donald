import asyncio
from pathlib import Path

import muffin
import pytest
from asgi_tools.tests import manage_lifespan


@pytest.fixture
def aiolib():
    return ("asyncio", {"use_uvloop": False})


@pytest.fixture
def app():
    return muffin.Application(DEBUG=True)


async def task1():
    return 42


async def ping():
    with open(Path(__file__).parent / "ping", "w") as f:
        f.write("PONG")
    print("PONG")


async def test_start(app):
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
        await asyncio.sleep(3e-1)

    with open(Path(__file__).parent / "ping", "r") as f:
        assert f.read() == "PONG"

    assert not tasks.donald._started


async def test_connect(app):
    from muffin_donald import Plugin

    tasks = Plugin(app, queue=True, num_workers=2)
    async with manage_lifespan(app):
        assert tasks.donald.queue._connected
