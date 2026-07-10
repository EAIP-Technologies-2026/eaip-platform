"""RuntimeKernel integration — registers Analytics as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.analytics.aggregation import AggregationEngine
from eaip.analytics.dashboard import DashboardService
from eaip.analytics.health import AnalyticsHealthCheck
from eaip.analytics.kpi_engine import KpiEngine
from eaip.analytics.service import AnalyticsService
from eaip.analytics.telemetry import TelemetryCollector
from eaip.analytics.trends import TrendAnalyzer
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AnalyticsRuntimeModule:
    """RuntimeModule that registers the analytics subsystem with the kernel.

    On startup:
      - Creates AnalyticsService, TrendAnalyzer, AggregationEngine, KpiEngine,
        DashboardService, and TelemetryCollector.
      - Registers AnalyticsHealthCheck.
      - Registers analytics capability.

    On shutdown:
      - Cleans up resources.
    """

    name: str = "analytics"

    def __init__(
        self,
        analytics_service: AnalyticsService | None = None,
        trend_analyzer: TrendAnalyzer | None = None,
        aggregation_engine: AggregationEngine | None = None,
        kpi_engine: KpiEngine | None = None,
        dashboard_service: DashboardService | None = None,
        telemetry_collector: TelemetryCollector | None = None,
    ) -> None:
        self._analytics_service = analytics_service or AnalyticsService()
        self._trend_analyzer = trend_analyzer or TrendAnalyzer(analytics_service=self._analytics_service)
        self._aggregation_engine = aggregation_engine or AggregationEngine(analytics_service=self._analytics_service)
        self._kpi_engine = kpi_engine or KpiEngine(analytics_service=self._analytics_service)
        self._dashboard_service = dashboard_service or DashboardService(analytics_service=self._analytics_service)
        self._telemetry_collector = telemetry_collector or TelemetryCollector(analytics_service=self._analytics_service)
        self._health_check = AnalyticsHealthCheck(analytics_service=self._analytics_service)
        self._log = get_logger("eaip.analytics.integration")

    @property
    def analytics_service(self) -> AnalyticsService:
        return self._analytics_service

    @property
    def trend_analyzer(self) -> TrendAnalyzer:
        return self._trend_analyzer

    @property
    def aggregation_engine(self) -> AggregationEngine:
        return self._aggregation_engine

    @property
    def kpi_engine(self) -> KpiEngine:
        return self._kpi_engine

    @property
    def dashboard_service(self) -> DashboardService:
        return self._dashboard_service

    @property
    def telemetry_collector(self) -> TelemetryCollector:
        return self._telemetry_collector

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("analytics.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(Capability(
            name="analytics:engine",
            title="Analytics Engine",
            status=CapabilityStatus.ENABLED,
            tags=("analytics", "engine"),
        ))
        kernel.platform.capabilities.register(Capability(
            name="analytics:kpi",
            title="KPI Engine",
            status=CapabilityStatus.ENABLED,
            tags=("analytics", "kpi"),
        ))
        kernel.platform.capabilities.register(Capability(
            name="analytics:dashboard",
            title="Dashboard Service",
            status=CapabilityStatus.ENABLED,
            tags=("analytics", "dashboard"),
        ))

        kernel.register_module("analytics.service", self._analytics_service)
        kernel.register_module("analytics.trends", self._trend_analyzer)
        kernel.register_module("analytics.aggregation", self._aggregation_engine)
        kernel.register_module("analytics.kpi", self._kpi_engine)
        kernel.register_module("analytics.dashboard", self._dashboard_service)
        kernel.register_module("analytics.telemetry", self._telemetry_collector)

        self._log.info(
            "analytics.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("analytics.module.stop")


__all__ = ["AnalyticsRuntimeModule"]
