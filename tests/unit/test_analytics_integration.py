"""Tests for AnalyticsRuntimeModule integration."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from eaip.analytics.aggregation import AggregationEngine
from eaip.analytics.dashboard import DashboardService
from eaip.analytics.integration import AnalyticsRuntimeModule
from eaip.analytics.kpi_engine import KpiEngine
from eaip.analytics.service import AnalyticsService
from eaip.analytics.telemetry import TelemetryCollector
from eaip.analytics.trends import TrendAnalyzer


class MockKernel:
    def __init__(self) -> None:
        self.platform = MagicMock()
        self.platform.health = MagicMock()
        self.platform.capabilities = MagicMock()
        self._modules: dict[str, Any] = {}

    def register_module(self, name: str, module: Any) -> None:
        self._modules[name] = module


class TestAnalyticsRuntimeModule:
    def test_default_construction(self) -> None:
        module = AnalyticsRuntimeModule()
        assert module.name == "analytics"
        assert isinstance(module.analytics_service, AnalyticsService)
        assert isinstance(module.trend_analyzer, TrendAnalyzer)
        assert isinstance(module.aggregation_engine, AggregationEngine)
        assert isinstance(module.kpi_engine, KpiEngine)
        assert isinstance(module.dashboard_service, DashboardService)
        assert isinstance(module.telemetry_collector, TelemetryCollector)

    def test_construction_with_deps(self) -> None:
        svc = AnalyticsService()
        trends = TrendAnalyzer(analytics_service=svc)
        agg = AggregationEngine(analytics_service=svc)
        kpi = KpiEngine(analytics_service=svc)
        dash = DashboardService(analytics_service=svc)
        tel = TelemetryCollector(analytics_service=svc)
        module = AnalyticsRuntimeModule(
            analytics_service=svc, trend_analyzer=trends, aggregation_engine=agg,
            kpi_engine=kpi, dashboard_service=dash, telemetry_collector=tel,
        )
        assert module.analytics_service is svc
        assert module.trend_analyzer is trends
        assert module.aggregation_engine is agg
        assert module.kpi_engine is kpi
        assert module.dashboard_service is dash
        assert module.telemetry_collector is tel

    async def test_start_registers_health_and_capabilities(self) -> None:
        kernel = MockKernel()
        module = AnalyticsRuntimeModule()
        await module.start(kernel)

        assert kernel.platform.health.register.call_count == 1
        assert kernel.platform.capabilities.register.call_count == 3
        assert "analytics.service" in kernel._modules
        assert "analytics.trends" in kernel._modules
        assert "analytics.aggregation" in kernel._modules
        assert "analytics.kpi" in kernel._modules
        assert "analytics.dashboard" in kernel._modules
        assert "analytics.telemetry" in kernel._modules

    async def test_start_and_stop(self) -> None:
        kernel = MockKernel()
        module = AnalyticsRuntimeModule()
        await module.start(kernel)
        await module.stop(kernel)

    async def test_stop_does_not_raise(self) -> None:
        kernel = MockKernel()
        module = AnalyticsRuntimeModule()
        await module.stop(kernel)
