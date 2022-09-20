"""Support session with Muffin framework."""

import typing as t
from functools import partial

from muffin import Application
from muffin.plugins import BasePlugin

from donald import Donald, logger
from donald.worker import Worker

__version__ = "0.8.0"
__project__ = "muffin-donald"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


T = t.TypeVar("T", bound=t.Callable)
assert logger


class Plugin(BasePlugin):

    """Run periodic tasks."""

    # Can be customized on setup
    name = "tasks"
    defaults: t.Dict = {
        # Donald options
        "log_level": Donald.defaults["log_level"],
        "log_config": Donald.defaults["log_config"],
        "backend": Donald.defaults["backend"],
        "backend_params": Donald.defaults["backend_params"],
        "worker_params": Donald.defaults["worker_params"],
        # Muffin-donald specific options
        "worker_lifespan": False,
        "start_worker": False,
        "start_scheduler": False,
        "filelock": None,
    }

    donald: Donald
    worker: Worker

    def setup(self, app: Application, **options):  # noqa
        """Setup Donald tasks manager."""
        super().setup(app, **options)

        self.manager = Donald(
            log_level=self.cfg.log_level,
            log_config=self.cfg.log_config,
            backend=self.cfg.backend,
            backend_params=self.cfg.backend_params,
            worker_params=self.cfg.worker_params,
        )

        @app.manage(lifespan=True)
        async def tasks_scheduler():
            """Run tasks scheduler."""
            if not self.cfg.start_scheduler:
                await self.manager.scheduler.start()

            await self.manager.scheduler.wait()

        @app.manage(lifespan=True)
        async def tasks_worker(scheduler=False):
            """Run tasks worker."""
            # Auto setup Sentry
            worker_params = self.manager._params["worker_params"]
            if not worker_params.get("on_error"):
                sentry = app.plugins.get("sentry")
                if sentry:
                    self.on_error(sentry.captureException)

            # Setup on_start/on_stop
            if self.cfg.worker_lifespan:
                if not worker_params.get("on_start"):
                    self.on_start(partial(app.lifespan.run, "startup"))

                if not worker_params.get("on_stop"):
                    self.on_stop(partial(app.lifespan.run, "shutdown"))

            if self.worker is None:
                self.worker = self.manager.create_worker(show_banner=True)
                self.worker.start()

            if scheduler:
                self.manager.scheduler.start()

            await self.worker.wait()

    async def startup(self):
        """Startup self tasks manager."""

        manager = self.manager
        worker_params = manager._params["worker_params"]

        # Auto setup Sentry
        if not worker_params.get("on_error"):
            sentry = self.app.plugins.get("sentry")
            if sentry:
                self.on_error(sentry.captureException)

        if not (worker_params.get("on_start") and worker_params.get("on_stop")):
            pass

        await manager.start()

        if self.cfg.start_worker:
            self.worker = manager.create_worker()
            self.worker.start()

        if self.cfg.start_scheduler:
            manager.scheduler.start()

    async def shutdown(self):
        """Shutdown self tasks manager."""
        manager = self.manager
        if self.worker is not None:
            await self.worker.stop()

        await manager.scheduler.stop()
        await manager.stop()

    def task(self, *args, **kwargs):
        """Register a task."""
        return self.manager.task(*args, **kwargs)

    def schedule(self, *args, **kwargs):
        """Schedule a task."""
        return self.manager.schedule(*args, **kwargs)

    def on_error(self, fn: T) -> T:
        """Register an error handler."""
        self.manager.on_error(fn)
        return fn

    def on_start(self, fn: T) -> T:
        """Register an error handler."""
        self.manager.on_start(fn)
        return fn

    def on_stop(self, fn: T) -> T:
        """Register an error handler."""
        self.manager.on_stop(fn)
        return fn
