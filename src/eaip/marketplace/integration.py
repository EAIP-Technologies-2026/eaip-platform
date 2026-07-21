"""Integration layer — MarketplaceRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.health.checks import HealthCheck
from eaip.logging.context import get_logger
from eaip.marketplace.health import MarketplaceHealthCheck
from eaip.marketplace.registry import MarketplaceRegistry

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class MarketplaceRuntimeModule:
    """RuntimeModule that bootstraps the marketplace subsystem during kernel start."""

    name: str = "marketplace"

    def __init__(
        self,
        registry: MarketplaceRegistry | None = None,
    ) -> None:
        self._registry = registry or MarketplaceRegistry()
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.marketplace.integration")

    @property
    def registry(self) -> MarketplaceRegistry:
        return self._registry

    @property
    def startup_duration(self) -> float:
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        t0 = time.monotonic()
        self._log.info("marketplace.integration.start")

        if kernel is not None:
            kernel.platform.health.register(self._health_check())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "marketplace.integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        self._log.info("marketplace.integration.stop")
        self._started = False

    def _health_check(self) -> HealthCheck:
        return MarketplaceHealthCheck(
            package_count=len(self._registry),
            active_installations=0,
        )


__all__ = ["MarketplaceRuntimeModule"]
