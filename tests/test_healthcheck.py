import pytest
from asgi_tools.tests import manage_lifespan

from .conftest import app


async def test_worker_healthcheck():
    healthcheck = app.manage.commands["tasks-worker-health"]

    with pytest.raises(SystemExit):
        assert await healthcheck()

    async with manage_lifespan(app):
        assert await healthcheck()


async def test_scheduler_healthcheck():
    healthcheck = app.manage.commands["tasks-scheduler-health"]

    with pytest.raises(SystemExit):
        assert await healthcheck()

    async with manage_lifespan(app):
        assert await healthcheck()
