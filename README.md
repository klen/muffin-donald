# Muffin-Donald

**Muffin-Donald** is a plugin for the [Muffin](https://github.com/klen/muffin) framework that provides support for asynchronous background tasks, workers, and scheduling.

[![Tests Status](https://github.com/klen/muffin-donald/workflows/tests/badge.svg)](https://github.com/klen/muffin-donald/actions)
[![PyPI Version](https://img.shields.io/pypi/v/muffin-donald)](https://pypi.org/project/muffin-donald/)
[![Python Versions](https://img.shields.io/pypi/pyversions/muffin-donald)](https://pypi.org/project/muffin-donald/)

## Features

- ✅ Register async tasks
- ✅ Run background workers
- ✅ Schedule periodic tasks (cron or intervals)
- ✅ RPC-style submit and wait for result
- ✅ Muffin plugin integration with lifecycle management

## Requirements

- python >= 3.11
- muffin >= 0.60.0
- donald >= 0.1.0

## Installation

```bash
pip install muffin-donald
```

## Usage

Initialize the plugin:

```python
import muffin
from muffin_donald import Plugin

app = muffin.Application("example")

tasks = Plugin(app, backend="redis", backend_params={
    "url": "redis://localhost:6379/0"
}, start_worker=True, start_scheduler=True)
```

Register a task:

```python
@tasks.task()
async def my_task(x, y):
    return x + y
```

Submit task for background execution:

```python
my_task.submit(1, 2)
```

Submit and wait for result (RPC style):

```python
result = await my_task.submit_and_wait(1, 2)
print("Result:", result)  # Result: 3
```

Schedule a periodic task:

```python
@tasks.task()
async def periodic_task():
    print("Periodic task executed")

periodic_task.schedule("*/5 * * * *")  # every 5 minutes
```

Handle task errors with `on_error`:

```python
@tasks.on_error
async def handle_error(exc):
    print("Task error:", exc)
```

Lifecycle hooks:

```python
@tasks.on_start
async def startup():
    print("Tasks manager started")

@tasks.on_stop
async def shutdown():
    print("Tasks manager stopped")
```

Healthcheck commands:

```bash
muffin <app> tasks-worker-health
muffin <app> tasks-scheduler-health
```

- Returns exit code 0 if healthy
- Returns exit code 1 if unhealthy

## Commands

| Command                | Description            |
|------------------------|------------------------|
| tasks-worker           | Run the worker process |
| tasks-scheduler        | Run the scheduler      |
| tasks-worker-health    | Check worker health    |
| tasks-scheduler-health | Check scheduler health |

## Configuration Options

You can configure the plugin via parameters or Muffin settings (with `TASKS_` prefix):

| Name            | Default | Description                       |
|-----------------|---------|-----------------------------------|
| log_level       | INFO    | Logger level                      |
| log_config      | None    | Logger config                     |
| backend         | memory  | Backend: memory, redis, amqp      |
| backend_params  | {}      | Backend connection params         |
| worker_params   | {}      | Worker params                     |
| start_worker    | False   | Auto start a worker on startup    |
| start_scheduler | False   | Auto start a scheduler on startup |

Example in Muffin settings:

```python
TASKS_BACKEND = "redis"
TASKS_BACKEND_PARAMS = {"url": "redis://localhost:6379/0"}
TASKS_START_WORKER = True
TASKS_START_SCHEDULER = True
```

## Testing

Example using `manage_lifespan`:

```python
import pytest
from asgi_tools.tests import manage_lifespan

async def test_tasks(app, tasks):
    async with manage_lifespan(app):
        result = await my_task.submit_and_wait(1, 2)
        assert result == 3
```

## Bug Tracker

Please report issues or suggestions at <https://github.com/klen/muffin-donald/issues>

## Contributing

Development happens at: <https://github.com/klen/muffin-donald>

## Contributors

- [klen](https://github.com/klen) (Kirill Klenov)

## License

Licensed under the MIT license.
