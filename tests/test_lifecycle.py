from asgi_tools.tests import manage_lifespan

from .conftest import app, tasks


async def test_shutdown_cleanup():
    async with manage_lifespan(app):
        assert tasks.worker is not None
    assert not tasks.manager.ready.is_set()
    assert tasks.worker is None or not tasks.worker._tasks
