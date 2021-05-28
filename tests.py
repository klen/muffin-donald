import muffin
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


async def test_base(app):
    from muffin_donald import Plugin

    tasks = Plugin(app, num_workers=2)
    assert tasks
    assert tasks.donald

    async with manage_lifespan(app):
        assert tasks.donald._started
        assert len(tasks.donald.workers) == 2
        res = await tasks.submit(task1)
        assert res == 42

    assert not tasks.donald._started
