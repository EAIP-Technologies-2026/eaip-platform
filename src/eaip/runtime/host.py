"""Host runtime entry point with async run_forever and signal handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.core.signals import ShutdownSignal, install_shutdown_handlers
from eaip.logging.context import get_logger
from eaip.runtime.kernel import RuntimeKernel

if TYPE_CHECKING:
    from eaip.platform.platform import Platform


async def run_forever(
    platform: Platform,
    *,
    install_signals: bool = True,
) -> None:
    """Boot the kernel on *platform* and run until a shutdown signal is received."""
    log = get_logger("eaip.runtime.host")
    kernel = RuntimeKernel(platform)
    shutdown = ShutdownSignal()
    if install_signals:
        install_shutdown_handlers(shutdown)

    await kernel.boot()
    try:
        log.info("host.running", phase=str(kernel.phase))
        await shutdown.wait()
    finally:
        await kernel.shutdown()
    log.info("host.stopped")


class Host:
    """Async context manager that boots and serves a RuntimeKernel."""

    def __init__(self, platform: Platform) -> None:
        """Wrap the platform and create the kernel."""
        self._platform = platform
        self._kernel = RuntimeKernel(platform)
        self._log = get_logger("eaip.runtime.host")

    @property
    def kernel(self) -> RuntimeKernel:
        """Return the underlying kernel."""
        return self._kernel

    async def start(self) -> None:
        """Boot the kernel."""
        await self._kernel.boot()

    async def stop(self) -> None:
        """Shut down the kernel."""
        await self._kernel.shutdown()

    async def serve(self, shutdown: ShutdownSignal | None = None) -> None:
        """Boot and wait for shutdown signal, then clean up."""
        sig = shutdown or ShutdownSignal()
        await self._kernel.boot()
        self._log.info("host.serving")
        try:
            await sig.wait()
        finally:
            await self._kernel.shutdown()

    async def __aenter__(self) -> Host:
        """Start on context entry."""
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Stop on context exit."""
        await self.stop()
