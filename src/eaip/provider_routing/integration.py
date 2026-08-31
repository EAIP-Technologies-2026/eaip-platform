"""Runtime integration — ProviderRoutingRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.provider_routing.health import ProviderRoutingHealthCheck
from eaip.provider_routing.service import ProviderRoutingService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ProviderRoutingRuntimeModule:
    """RuntimeModule that bootstraps the provider routing subsystem during kernel start.

    On start:
      - Creates the routing service.
      - Registers the provider routing health check.
    On stop:
      - Cleans up any in-flight state.
    """

    name: str = "provider_routing"

    def __init__(
        self,
        service: ProviderRoutingService | None = None,
    ) -> None:
        """Initialize the ProviderRoutingRuntimeModule.

        Args:
            service: An optional pre-configured routing service.
        """
        self._service = service or ProviderRoutingService()
        self._log = get_logger("eaip.provider_routing.integration")
        self._startup_duration: float = 0.0

    @property
    def service(self) -> ProviderRoutingService:
        """Return the configured routing service."""
        return self._service

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel) -> None:
        """Bootstrap the provider routing subsystem.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("provider_routing.module.start")
        t0 = time.monotonic()

        check = ProviderRoutingHealthCheck(self._service)
        kernel.platform.health.register(check)

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "provider_routing.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the provider routing subsystem.

        Args:
            _kernel: The runtime kernel.
        """
        self._log.info("provider_routing.module.stop")
        self._log.info("provider_routing.module.stopped")


__all__ = ["ProviderRoutingRuntimeModule"]
