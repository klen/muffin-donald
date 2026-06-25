from pathlib import Path

import muffin
import pytest

from muffin_donald import Plugin, logger

PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def aiolib():
    return ("asyncio", {"loop_factory": None})


app = muffin.Application(DEBUG=True)
tasks = Plugin(app, start_worker=True, start_scheduler=True)


@tasks.task()
async def task1():
    logger.info("Task1: done")
    return 42


@tasks.task()
async def fail_task():
    raise ValueError("expected failure")


@tasks.task()
async def ping():
    PROJECT_ROOT.joinpath("ping").write_text("PONG")
    logger.info("Ping: done")


ping.schedule(2e-1)


@tasks.task()
async def immediate_task():
    logger.info("Immediate task ran")
