"""Runtime module integration for the Health Aggregator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.healthagg.aggregator import HealthAggregator
from eaip.healthagg.dependencies import DependencyGraph
from eaip.healthagg.health import HealthAggHealthCheck
from eaip.healthagg.models import HealthAggregationConfig
from eaip.healthagg.status_page import StatusPageService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class HealthAggRuntimeModule:
    name: str = "healthagg"

    def __init__(
        self,
        config: HealthAggregationConfig | None = None,
        aggregator: HealthAggregator | None = None,
        dependency_graph: DependencyGraph | None = None,
        status_page_service: StatusPageService | None = None,
    ) -> None:
        self._config = config or HealthAggregationConfig()
        self._graph = dependency_graph or DependencyGraph()
        self._aggregator = aggregator or HealthAggregator(
            config=self._config, dependency_graph=self._graph
        )
        self._status_page_service = status_page_service or StatusPageService(
            aggregator=self._aggregator
        )
        self._log = get_logger("eaip.healthagg.integration")

    @property
    def config(self) -> HealthAggregationConfig:
        return self._config

    @property
    def aggregator(self) -> HealthAggregator:
        return self._aggregator

    @property
    def dependency_graph(self) -> DependencyGraph:
        return self._graph

    @property
    def status_page_service(self) -> StatusPageService:
        return self._status_page_service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("healthagg.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.healthagg",
            title="Health Check Aggregator",
            description="Advanced health aggregation with dependency graphs, status pages, and health history",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("health", "monitoring", "dependencies", "status-pages", "snapshots"),
        )
        platform.capabilities.register(capability)
        platform.health.register(HealthAggHealthCheck(aggregator=self._aggregator))
        self._log.info("healthagg.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("healthagg.module.stopping")


__all__ = ["HealthAggRuntimeModule"]
