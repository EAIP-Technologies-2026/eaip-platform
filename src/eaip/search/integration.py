"""Integration layer — SearchRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.search.engine import EnterpriseSearchEngine
from eaip.search.federation import SearchFederation
from eaip.search.health import SearchHealthCheck
from eaip.search.ranking import RankingService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SearchRuntimeModule:
    """RuntimeModule that bootstraps the Enterprise Search subsystem
    during kernel start.

    Registers health checks, capabilities, and exposes the search
    engine and federation to other components.
    """

    name: str = "search"

    def __init__(
        self,
        engine: EnterpriseSearchEngine | None = None,
        federation: SearchFederation | None = None,
        ranking_service: RankingService | None = None,
    ) -> None:
        """Initialize the SearchRuntimeModule.

        Args:
            engine: Optional EnterpriseSearchEngine instance.
            federation: Optional SearchFederation instance.
            ranking_service: Optional RankingService instance.
        """
        self._engine = engine or EnterpriseSearchEngine()
        self._federation = federation or SearchFederation()
        self._ranking_service = ranking_service or RankingService()
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.search.integration")

    @property
    def engine(self) -> EnterpriseSearchEngine:
        """Return the EnterpriseSearchEngine."""
        return self._engine

    @property
    def federation(self) -> SearchFederation:
        """Return the SearchFederation."""
        return self._federation

    @property
    def ranking_service(self) -> RankingService:
        """Return the RankingService."""
        return self._ranking_service

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the search module.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("search.integration.start")

        provider_count = len(self._engine.providers)

        if kernel is not None:
            kernel.platform.health.register(self._health_check(provider_count))
            kernel.platform.capabilities.register(self._capability())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "search.integration.complete",
            duration_s=round(self._startup_duration, 3),
            providers=provider_count,
        )

    async def stop(self, kernel: RuntimeKernel | None = None) -> None:
        """Stop the search module."""
        self._log.info("search.integration.stop")
        self._started = False

    async def register_with_runtime(self) -> None:
        """Register with the EAIP runtime."""
        self._log.info("search.integration.register")

    def _health_check(self, provider_count: int) -> HealthCheck:
        return SearchHealthCheck(provider_count=provider_count)

    def _capability(self) -> Capability:
        return Capability(
            name="search:engine",
            title="Enterprise Search Engine",
            status=CapabilityStatus.ENABLED,
        )


__all__ = ["SearchRuntimeModule"]
