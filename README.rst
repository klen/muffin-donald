Muffin-Donald
#############

.. _description:

**Muffin-Donald** -- Its a plugin for Muffin_ framework which provides support
for asyncronous tasks

.. _badges:

.. image:: https://github.com/klen/muffin-donald/workflows/tests/badge.svg
    :target: https://github.com/klen/muffin-donald/actions
    :alt: Tests Status

.. image:: https://img.shields.io/pypi/v/muffin-donald
    :target: https://pypi.org/project/muffin-donald/
    :alt: PYPI Version

.. image:: https://img.shields.io/pypi/pyversions/muffin-donald
    :target: https://pypi.org/project/muffin-donald/
    :alt: Python Versions

.. _contents:

.. contents::

.. _requirements:

Requirements
=============

- python >= 3.7

.. _installation:

Installation
=============

**Muffin-Donald** should be installed using pip: ::

    pip install muffin-donald

.. _usage:

Usage
=====


Initialize and setup the plugin:

.. code-block:: python

    import muffin
    import muffin_donald

    # Create Muffin Application
    app = muffin.Application('example')

    # Initialize the plugin
    # As alternative: tasks = muffin_donald.Plugin(app, **options)
    tasks = muffin_donald.Plugin()
    donald.setup(app)


And etc

Options
-------

=========================== =========================== =========================== 
Name                        Default value               Desctiption
--------------------------- --------------------------- ---------------------------
**autostart**               ``True``                    Auto start tasks workers
**fake_mode**               ``False``                   Run tasks immediately (testing)
**num_workers**             ``<CPU_COUNT> - 1``         Number of workers
**max_tasks_per_worker**    ``100``                     Maximum concurent tasks per worker
**filelock**                ``None``                    File lock path
**loglevel**                ``INFO``                    Logger Level
**queue_exchange**          ``tasks``                   Tasks queue exchange
**queue_name**              ``tasks``                   Tasks queue name
**queue_params**            ``{}``                      Queue params
=========================== =========================== =========================== 


You are able to provide the options when you are initiliazing the plugin:

.. code-block:: python

    donald.setup(app, num_workers=2)


Or setup it inside ``Muffin.Application`` config using the ``DONALD_`` prefix:

.. code-block:: python

   DONALD_ROOT_URL = 'https://api.github.com'

``Muffin.Application`` configuration options are case insensitive


.. _bugtracker:

Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/muffin-donald/issues

.. _contributing:

Contributing
============

Development of Muffin-Donald happens at: https://github.com/klen/muffin-donald


Contributors
=============

* klen_ (Kirill Klenov)

.. _license:

License
========

Licensed under a `MIT license`_.

.. _links:


.. _klen: https://github.com/klen
.. _Muffin: https://github.com/klen/muffin

.. _MIT license: http://opensource.org/licenses/MIT
