"""Support session with Muffin framework."""

from __future__ import annotations

from inspect import iscoroutinefunction
from typing import TYPE_CHECKING, Any, ClassVar, ParamSpec, TypeVar

from donald import Donald, logger
from muffin.plugins import BasePlugin

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping
    from typing import Unpack

    from donald.manager import TInterval, TVWorkerOnErrFn, TVWorkerOnFn
    from donald.tasks import TaskWrapper
    from donald.types import TTaskParamsPartial, TWorkerOnErrFn
    from donald.worker import Worker
    from muffin import Application

P = ParamSpec("P")
R = TypeVar("R")

assert logger


class Plugin(BasePlugin):
    """Run periodic tasks."""

    # Can be customized on setup
    name = "tasks"
    defaults: ClassVar[Mapping[str, Any]] = {
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
    worker: Worker | None = None

    def setup(
        self,
        app: "Application",
        *,
        name: str | None = None,
        **options: Any,
    ) -> bool:
        """Setup Donald tasks manager."""
        result = super().setup(app, name=name, **options)

        self.manager = Donald(
            log_level=self.cfg.log_level,
            log_config=self.cfg.log_config,
            backend=self.cfg.backend,
            backend_params=self.cfg.backend_params,
            worker_params=self.cfg.worker_params,
        )

        @app.manage(lifespan=True, name=f"{self.name}-worker")
        async def worker(*, scheduler: bool = False) -> None:
            """Run tasks worker."""
            # Auto setup Sentry
            setup_on_error(self)

            worker = self.manager.create_worker(show_banner=True)
            worker.start()

            if scheduler:
                self.manager.scheduler.start()

            await worker.wait()

        @app.manage(lifespan=False, name=f"{self.name}-worker-health")
        async def worker_healthcheck(timeout_sec: float = 10) -> bool:
            """Run tasks healthcheck."""
            async with self.manager:
                is_healthy = await self.manager.healthcheck(timeout=timeout_sec)
                if not is_healthy:
                    logger.error("Tasks manager is unhealthy")
                    raise SystemExit(1)
            return is_healthy

        @app.manage(lifespan=False, name=f"{self.name}-scheduler")
        async def scheduler() -> None:
            """Run tasks scheduler."""
            async with self.manager:
                scheduler = self.manager.scheduler
                if not self.cfg.start_scheduler:
                    scheduler.start()

                await scheduler.wait()

        @app.manage(lifespan=False, name=f"{self.name}-scheduler-health")
        async def scheduler_healthcheck() -> bool:
            """Run tasks scheduler healthcheck."""
            async with self.manager:
                is_healthy = await self.manager.scheduler_healthcheck()
                if not is_healthy:
                    logger.error("Tasks scheduler is unhealthy")
                    raise SystemExit(1)
            return is_healthy

        return result

    async def startup(self) -> None:
        """Startup self tasks manager."""

        setup_on_error(self)

        manager = self.manager
        await manager.start()

        if self.cfg.start_worker:
            self.worker = manager.create_worker()
            self.worker.start()

        if self.cfg.start_scheduler:
            manager.scheduler.start()

    async def shutdown(self) -> None:
        """Shutdown self tasks manager."""
        manager = self.manager
        if self.worker is not None:
            await self.worker.stop()

        if self.cfg.start_scheduler:
            await manager.scheduler.stop()
        await manager.stop()

    def task(
        self,
        fn: Any = ...,
        /,
        **params: "Unpack[TTaskParamsPartial]",
    ) -> "Callable[[Callable[P, Awaitable[R]]], TaskWrapper[P, R]]":
        """Decorator to wrap a coroutine function into a Task object."""
        return self.manager.task(fn, **params)

    def schedule(
        self,
        interval: "TInterval",
    ) -> "Callable[[TaskWrapper[P, R]], TaskWrapper[P, R]]":
        """Schedule a task."""
        return self.manager.schedule(interval)

    def on_error(self, fn: "TVWorkerOnErrFn") -> "TWorkerOnErrFn":
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


def setup_on_error(plugin: Plugin) -> None:
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

            async def on_error(exc: BaseException) -> None:
                sentry.capture_exception(exc)

            plugin.on_error(on_error)
