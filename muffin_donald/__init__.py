"""Support session with Muffin framework."""

import typing as t

from donald import Donald
from muffin import Application
from muffin.plugins import BasePlugin


__version__ = "0.0.2"
__project__ = "muffin-donald"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


T = t.TypeVar('T', bound=t.Callable)


class Plugin(BasePlugin):

    """Run periodic tasks."""

    # Can be customized on setup
    name = 'tasks'
    defaults: t.Dict = {
        "autostart": True,
        "fake_mode": Donald.defaults['fake_mode'],
        "num_workers": Donald.defaults['num_workers'],
        "max_tasks_per_worker": Donald.defaults['max_tasks_per_worker'],
        "filelock": Donald.defaults['filelock'],
        "loglevel": Donald.defaults['loglevel'],
        "queue": False,
        "queue_exchange": 'tasks',
        "queue_name": 'tasks',
    }

    donald: Donald = None
    __exc_handler: t.Optional[t.Callable] = None

    def setup(self, app: Application, **options):
        """Setup Donald tasks manager."""
        super().setup(app, **options)
        self.donald = Donald(
            fake_mode=self.cfg.fake_mode,
            filelock=self.cfg.filelock,
            loglevel=self.cfg.loglevel,
            num_workers=self.cfg.num_workers,
            queue=self.cfg.queue,
            queue_name=self.cfg.queue_name,
            queue_exchange=self.cfg.queue_exchange,
        )
        if self.__exc_handler:
            self.donald.on_exception(self.__exc_handler)

    def __getattr__(self, name):
        """Proxy attributes to the tasks manager."""
        return getattr(self.donald, name)

    def on_error(self, fn: T) -> T:
        """Register an error handler."""
        self.__exc_handler = fn
        return fn

    async def startup(self):
        """Startup self tasks manager."""
        donald = t.cast(Donald, self.donald)

        started = False
        if self.cfg.autostart:
            started = await donald.start()

        if donald.queue:
            await donald.queue.connect()
            if started:
                await donald.queue.start()

    async def shutdown(self):
        """Shutdown self tasks manager."""
        donald = t.cast(Donald, self.donald)
        await donald.stop()
        await donald.queue.stop()
