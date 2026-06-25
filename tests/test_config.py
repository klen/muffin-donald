from muffin_donald import Plugin

from .conftest import app


def test_plugin_setup_defaults():
    plugin = Plugin(app, backend="memory", start_worker=True)
    assert plugin.cfg.backend == "memory"
    assert plugin.cfg.start_worker is True


def test_base():
    assert "tasks-worker" in app.manage.commands
    assert "tasks-scheduler" in app.manage.commands
    assert "tasks-worker-health" in app.manage.commands
    assert "tasks-scheduler-health" in app.manage.commands
