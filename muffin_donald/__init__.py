"""Support session with Muffin framework."""

from muffin import Application
from muffin.plugins import BasePlugin

from donald import Donald, logger
from donald.manager import TInterval, TVWorkerOnErrFn, TVWorkerOnFn
from donald.worker import Worker

__version__ = "0.9.1"
__project__ = "muffin-donald"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


assert logger


class Plugin(BasePlugin):

    """Run periodic tasks."""

    # Can be customized on setup
    name = "tasks"
    defaults = {
        # Donald options
        "log_level": Donald.defaults["log_level"],
        "log_config": Donald.defaults["log_config"],
        "backend": Donald.defaults["backend"],
        "backend_params": Donald.defaults["backend_params"],
        "worker_params": Donald.defaults["worker_params"],
        # Muffin-donald specific options
        "start_worker": False,
        "start_scheduler": False,
        "filelock": None,
    }

    manager: Donald
    worker: Worker = None

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
                self.manager.scheduler.start()

            await self.manager.scheduler.wait()

        @app.manage(lifespan=True)
        async def tasks_worker(scheduler=False):
            """Run tasks worker."""
            # Auto setup Sentry
            worker_params = self.manager._params["worker_params"]
            if not worker_params.get("on_error"):
                sentry = app.plugins.get("sentry")
                if sentry:

                    async def on_error(exc):
                        sentry.captureException(exc)

                    self.on_error(on_error)

            worker = self.manager.create_worker(show_banner=True)
            worker.start()

            if scheduler:
                self.manager.scheduler.start()

            await worker.wait()

    async def startup(self):
        """Startup self tasks manager."""

        manager = self.manager
        worker_params = manager._params["worker_params"]

        # Auto setup Sentry
        if not worker_params.get("on_error"):
            sentry = self.app.plugins.get("sentry")
            if sentry:
                self.on_error(sentry.captureException)

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

        if self.cfg.start_scheduler:
            await manager.scheduler.stop()
        await manager.stop()

    def task(self, *args, **kwargs):
        """Register a task."""
        return self.manager.task(*args, **kwargs)

    def schedule(self, interval: TInterval):
        """Schedule a task."""
        return self.manager.schedule(interval)

    def on_error(self, fn: TVWorkerOnErrFn) -> TVWorkerOnErrFn:
        """Register an error handler."""
        self.manager.on_error(fn)
        return fn

    def on_start(self, fn: TVWorkerOnFn) -> TVWorkerOnFn:
        """Register an error handler."""
        self.manager.on_start(fn)
        return fn

    def on_stop(self, fn: TVWorkerOnFn) -> TVWorkerOnFn:
        """Register an error handler."""
        self.manager.on_stop(fn)
        return fn
