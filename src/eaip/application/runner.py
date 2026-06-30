"""Async runner — handles signal-driven graceful shutdown."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from eaip.core.signals import ShutdownSignal, install_shutdown_handlers
from eaip.logging.context import get_logger
from eaip.platform.platform import Platform

OnRunning = Callable[[Platform], Awaitable[None]]


async def run_platform(
    platform: Platform,
    *,
    on_running: OnRunning | None = None,
    install_signals: bool = True,
) -> None:
    """Start ``platform``, optionally invoke ``on_running``, await shutdown.

    Behaviour
    ---------
    1. Install ``SIGINT`` / ``SIGTERM`` handlers (unless ``install_signals=False``).
    2. ``await platform.start()``.
    3. ``await on_running(platform)`` if provided.
    4. ``await shutdown_signal.wait()`` — block until a signal triggers it.
    5. ``await platform.stop()`` — always, even if ``on_running`` raises.
    """
    log = get_logger("eaip.application.runner")
    shutdown = ShutdownSignal()
    if install_signals:
        install_shutdown_handlers(shutdown)

    await platform.start()
    try:
        if on_running is not None:
            await on_running(platform)
        if not shutdown.is_set():
            log.info("application.awaiting_shutdown")
            await shutdown.wait()
    finally:
        await platform.stop()


__all__ = ["OnRunning", "run_platform"]
