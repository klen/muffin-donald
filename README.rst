Muffin-Donald
#############

**Muffin-Donald** is a plugin for the Muffin_ framework that provides support
for asynchronous background tasks, workers, and scheduling.

.. image:: https://github.com/klen/muffin-donald/workflows/tests/badge.svg
    :target: https://github.com/klen/muffin-donald/actions
    :alt: Tests Status

.. image:: https://img.shields.io/pypi/v/muffin-donald
    :target: https://pypi.org/project/muffin-donald/
    :alt: PYPI Version

.. image:: https://img.shields.io/pypi/pyversions/muffin-donald
    :target: https://pypi.org/project/muffin-donald/
    :alt: Python Versions

Contents
========

.. contents::

Features
========

- ✅ Register async tasks
- ✅ Run background workers
- ✅ Schedule periodic tasks (cron or intervals)
- ✅ RPC-style submit and wait for result
- ✅ Muffin plugin integration with lifecycle management

Requirements
============

- python >= 3.10
- muffin >= 0.60.0
- donald >= 0.1.0

Installation
============

Install via pip::

    pip install muffin-donald

Usage
=====

Initialize the plugin:

.. code-block:: python

    import muffin
    from muffin_donald import Plugin

    app = muffin.Application("example")

    tasks = Plugin(app, backend="redis", backend_params={
        "url": "redis://localhost:6379/0"
    }, start_worker=True, start_scheduler=True)

Register a task:

.. code-block:: python

    @tasks.task()
    async def my_task(x, y):
        return x + y

Submit task for background execution:

.. code-block:: python

    my_task.submit(1, 2)

Submit and wait for result (RPC style):

.. code-block:: python

    result = await my_task.submit_and_wait(1, 2)
    print("Result:", result)  # Result: 3

Schedule a periodic task:

.. code-block:: python

    @tasks.task()
    async def periodic_task():
        print("Periodic task executed")

    periodic_task.schedule("*/5 * * * *")  # every 5 minutes

Handle task errors with on_error:

.. code-block:: python

    @tasks.on_error
    async def handle_error(exc):
        print("Task error:", exc)

Lifecycle hooks:

.. code-block:: python

    @tasks.on_start
    async def startup():
        print("Tasks manager started")

    @tasks.on_stop
    async def shutdown():
        print("Tasks manager stopped")

Healthcheck command:

Muffin-Donald provides a CLI command for health checks::

    muffin <app> tasks-healthcheck

- Returns exit code 0 if healthy
- Returns exit code 1 if unhealthy

Commands
========

+-------------------+-----------------------------+
| Command           | Description                 |
+===================+=============================+
| tasks-worker      | Run the worker process      |
+-------------------+-----------------------------+
| tasks-scheduler   | Run the scheduler           |
+-------------------+-----------------------------+
| tasks-healthcheck | Check manager health        |
+-------------------+-----------------------------+

Configuration Options
=====================

You can configure the plugin via parameters or Muffin settings (with ``TASKS_`` prefix):

+------------------+-----------+-------------------------------------+
| Name             | Default   | Description                         |
+==================+===========+=====================================+
| log_level        | INFO      | Logger level                        |
+------------------+-----------+-------------------------------------+
| log_config       | None      | Logger config                       |
+------------------+-----------+-------------------------------------+
| backend          | memory    | Backend: memory, redis, amqp        |
+------------------+-----------+-------------------------------------+
| backend_params   | {}        | Backend connection params           |
+------------------+-----------+-------------------------------------+
| worker_params    | {}        | Worker params                       |
+------------------+-----------+-------------------------------------+
| start_worker     | False     | Auto start a worker on startup      |
+------------------+-----------+-------------------------------------+
| start_scheduler  | False     | Auto start a scheduler on startup   |
+------------------+-----------+-------------------------------------+

Example in Muffin settings:

.. code-block:: python

    TASKS_BACKEND = "redis"
    TASKS_BACKEND_PARAMS = {"url": "redis://localhost:6379/0"}
    TASKS_START_WORKER = True
    TASKS_START_SCHEDULER = True

Testing
=======

Example using ``manage_lifespan``:

.. code-block:: python

    import pytest
    from asgi_tools.tests import manage_lifespan

    async def test_tasks(app, tasks):
        async with manage_lifespan(app):
            result = await my_task.submit_and_wait(1, 2)
            assert result == 3

Bug Tracker
===========

Please report issues or suggestions at https://github.com/klen/muffin-donald/issues

Contributing
============

Development happens at: https://github.com/klen/muffin-donald

Contributors
============

- klen_ (Kirill Klenov)

License
=======

Licensed under the MIT license.

.. _klen: https://github.com/klen
.. _Muffin: https://github.com/klen/muffin
