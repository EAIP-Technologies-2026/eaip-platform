"""Coordinated shutdown signal handling.

The Foundation does not impose a particular event loop; consumers wire the
shutdown handlers into whichever runtime (asyncio, anyio, FastAPI, …) they
prefer. The :class:`ShutdownSignal` is a simple ``asyncio.Event`` wrapper.
"""

from __future__ import annotations

import asyncio
import signal as _signal
from collections.abc import Iterable

from eaip.logging.context import get_logger


class ShutdownSignal:
    """Thin wrapper around :class:`asyncio.Event` for graceful shutdown."""

    def __init__(self) -> None:
        """Initialize ShutdownSignal with an unset asyncio event."""
        self._event = asyncio.Event()

    def trigger(self) -> None:
        """Trigger the shutdown event."""
        self._event.set()

    def is_set(self) -> bool:
        """Check if the shutdown event is set.

        Returns:
            True if set, False otherwise.
        """
        return self._event.is_set()

    async def wait(self) -> None:
        """Wait for the shutdown event to be set."""
        await self._event.wait()


def install_shutdown_handlers(
    signal_obj: ShutdownSignal,
    *,
    signals: Iterable[int] = (_signal.SIGINT, _signal.SIGTERM),
) -> None:
    """Wire OS signals to trigger ``signal_obj`` on the running event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # pragma: no cover - defensive
        raise RuntimeError(
            "install_shutdown_handlers must be called from a running asyncio event loop"
        ) from None
    log = get_logger("eaip.core.signals")
    for sig in signals:
        try:
            loop.add_signal_handler(sig, _handler, signal_obj, sig, log)
        except NotImplementedError:  # pragma: no cover - e.g. Windows event loop
            log.warning("signals.unsupported", signal=int(sig))


def _handler(signal_obj: ShutdownSignal, sig: int, log: object) -> None:
    """Handle OS signal by triggering the shutdown event.

    Args:
        signal_obj: The shutdown signal object to trigger.
        sig: The signal integer.
        log: The logger instance.
    """
    # ``log`` is a structlog BoundLogger; typed as object to avoid circular imports.
    if hasattr(log, "info"):
        log.info("signals.received", signal=int(sig))
    signal_obj.trigger()


__all__ = ["ShutdownSignal", "install_shutdown_handlers"]
