"""Support session with Muffin framework."""

from __future__ import annotations

from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, ClassVar, Optional

from donald import Donald, logger
from muffin.plugins import BasePlugin

if TYPE_CHECKING:
    from donald.manager import TInterval, TVWorkerOnErrFn, TVWorkerOnFn
    from donald.worker import Worker
    from muffin import Application

assert logger


class Plugin(BasePlugin):
    """Run periodic tasks."""

    # Can be customized on setup
    name = "tasks"
    defaults: ClassVar = {
        # Donald options
        "log_level": Donald.defaults["log_level"],
        "log_config": Donald.defaults["log_config"],
        "backend": Donald.defaults["backend"],
        "backend_params": Donald.defaults["backend_params"],
        "worker_params": Donald.defaults["worker_params"],
        # Muffin-donald specific options
        "start_worker": False,
        "start_scheduler": False,
    }

    manager: Donald
    worker: Optional[Worker] = None

    def setup(self, app: "Application", **options):
        """Setup Donald tasks manager."""
        super().setup(app, **options)

        self.manager = Donald(
            log_level=self.cfg.log_level,
            log_config=self.cfg.log_config,
            backend=self.cfg.backend,
            backend_params=self.cfg.backend_params,
            worker_params=self.cfg.worker_params,
        )
        self.task = self.manager.task

        @app.manage(lifespan=True)
        async def tasks_scheduler():
            """Run tasks scheduler."""
            if not self.cfg.start_scheduler:
                self.manager.scheduler.start()

            await self.manager.scheduler.wait()

        @app.manage(lifespan=True)
        async def tasks_worker(*, scheduler=False):
            """Run tasks worker."""
            # Auto setup Sentry
            setup_on_error(self)

            worker = self.manager.create_worker(show_banner=True)
            worker.start()

            if scheduler:
                self.manager.scheduler.start()

            await worker.wait()

        @app.manage
        async def tasks_healthcheck(timeout=10):
            """Run tasks healthcheck."""
            async with self.manager:
                is_healthy = await self.manager.healthcheck(timeout=timeout)
                if not is_healthy:
                    logger.error("Tasks manager is unhealthy")
                    raise SystemExit(1)
            return is_healthy

    async def startup(self):
        """Startup self tasks manager."""

        setup_on_error(self)

        manager = self.manager
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

    def schedule(self, interval: "TInterval"):
        """Schedule a task."""
        return self.manager.schedule(interval)

    def on_error(self, fn: "TVWorkerOnErrFn") -> "TVWorkerOnErrFn":
        """Register an error handler."""
        assert iscoroutinefunction(fn), "on_error handler must be async function"
        self.manager.on_error(fn)
        return fn

    def on_start(self, fn: "TVWorkerOnFn") -> "TVWorkerOnFn":
        """Register an error handler."""
        self.manager.on_start(fn)
        return fn

    def on_stop(self, fn: "TVWorkerOnFn") -> "TVWorkerOnFn":
        """Register an error handler."""
        self.manager.on_stop(fn)
        return fn


def setup_on_error(plugin: Plugin):
    """Generate on_error handler for Donald."""
    manager = plugin.manager
    worker_params = manager._params["worker_params"]

    # Auto setup Sentry
    if not worker_params.get("on_error"):
        maybe_sentry = plugin.app.plugins.get("sentry")
        if maybe_sentry:
            from muffin_sentry.plugin import Plugin as Sentry  # noqa: PLC0415

            assert isinstance(
                maybe_sentry,
                Sentry,
            ), "Sentry plugin is not installed or not a valid instance"
            sentry: Sentry = maybe_sentry

            async def on_error(exc):
                sentry.capture_exception(exc)

            plugin.on_error(on_error)
