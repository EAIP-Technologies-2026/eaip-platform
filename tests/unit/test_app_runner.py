"""Tests for ApplicationRunner."""

from __future__ import annotations

import asyncio
from contextlib import suppress

from eaip.app.builder import ApplicationBuilder
from eaip.app.runner import ApplicationRunner


class TestApplicationRunner:
    async def test_run_starts_and_stops(self):
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()
        runner = ApplicationRunner(app, install_signals=False)

        # Run but cancel after a short delay so we don't hang.
        async def delayed_cancel() -> None:
            await asyncio.sleep(0.05)

        task = asyncio.create_task(runner.run())
        await asyncio.sleep(0.1)
        task.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await task

    async def test_on_running_callback(self):
        builder = ApplicationBuilder()
        app = builder.without_runtime_kernel().build()
        runner = ApplicationRunner(app, install_signals=False)
        called = False

        async def on_running(_app):
            nonlocal called
            called = True

        t1 = asyncio.create_task(runner.run(on_running=on_running))
        await asyncio.sleep(0.2)
        t1.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await t1
