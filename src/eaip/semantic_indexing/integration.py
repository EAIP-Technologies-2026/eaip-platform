"""Integration layer — wiring for the semantic indexing subsystem."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.semantic_indexing.events import SemanticIndexingEvent
from eaip.semantic_indexing.service import SemanticIndexingService

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SemanticIndexingRuntimeModule:
    """Runtime module for the semantic indexing subsystem.

    Provides lifecycle hooks so that the semantic indexing subsystem
    can be registered with the EAIP runtime.
    """

    name: str = "semantic_indexing"

    def __init__(
        self,
        service: SemanticIndexingService | None = None,
        **_kwargs: object,
    ) -> None:
        """Initialize the runtime module.

        Args:
            service: Optional SemanticIndexingService instance.
        """
        self._service = service
        self._started = service is not None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.semantic_indexing.integration")

    @property
    def service(self) -> SemanticIndexingService:
        """Return the underlying SemanticIndexingService."""
        if self._service is None:
            raise RuntimeError("SemanticIndexingService not initialized. Call start() first.")
        return self._service

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the semantic indexing integration.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("integration.start")

        if self._service is None:
            self._service = SemanticIndexingService()

        if kernel is not None:
            kernel.platform.health.register(self._name_check())
            kernel.platform.capabilities.register(self._name_capability())

        self._startup_duration = time.monotonic() - t0
        self._started = True
        self._log.info(
            "integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the semantic indexing integration."""
        self._log.info("integration.stop")
        self._started = False

    def on_event(self, handler: Any) -> None:
        """Register an event handler.

        Args:
            handler: A callable accepting a SemanticIndexingEvent.
        """
        service = self._service
        if service is not None:
            service.on(SemanticIndexingEvent, handler)

    def _name_check(self) -> HealthCheck:
        check_name = "semantic_indexing"

        class _SemanticIndexingHealthCheck:
            name: str = check_name

            async def check(self) -> HealthReport:
                return HealthReport(
                    component=check_name,
                    status=HealthStatus.HEALTHY,
                )

        return _SemanticIndexingHealthCheck()

    def _name_capability(self) -> Capability:
        return Capability(
            name="semantic_indexing:service",
            title="Semantic Indexing Service",
            status=CapabilityStatus.ENABLED,
        )


__all__ = ["SemanticIndexingRuntimeModule"]
