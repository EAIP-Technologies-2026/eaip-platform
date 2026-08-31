"""Tests for KpiEngine."""

from __future__ import annotations

import pytest

from eaip.analytics.kpi_engine import KpiEngine
from eaip.analytics.service import AnalyticsService
from eaip.analytics.trends import TrendAnalyzer
from eaip.goals.exceptions import KpiNotFoundError
from eaip.goals.models import KpiDefinition, KpiDirection
from eaip.goals.tracker import GoalTracker


class TestKpiEngine:
    @pytest.fixture
    def engine(self) -> KpiEngine:
        return KpiEngine()

    @pytest.fixture
    def seeded_engine(self) -> KpiEngine:
        tracker = GoalTracker()
        kpi1 = KpiDefinition(
            id="k1", name="Revenue", target_value=1000.0, direction=KpiDirection.HIGHER_IS_BETTER
        )
        kpi2 = KpiDefinition(
            id="k2", name="Latency", target_value=200.0, direction=KpiDirection.LOWER_IS_BETTER
        )
        tracker.register_kpi(kpi1)
        tracker.register_kpi(kpi2)
        svc = AnalyticsService()
        trends = TrendAnalyzer(analytics_service=svc)
        return KpiEngine(analytics_service=svc, goal_tracker=tracker, trend_analyzer=trends)

    class TestRecordKpiValue:
        async def test_records_value(self, seeded_engine: KpiEngine) -> None:
            prev = await seeded_engine.record_kpi_value("k1", 500.0)
            assert prev == 0.0
            result = await seeded_engine.get_kpi_status("k1")
            assert result["current_value"] == 500.0

        async def test_raises_on_unknown_kpi(self, engine: KpiEngine) -> None:
            with pytest.raises(KpiNotFoundError):
                await engine.record_kpi_value("unknown", 1.0)

    class TestEvaluateKpi:
        async def test_returns_met_when_above_target(self, seeded_engine: KpiEngine) -> None:
            result = await seeded_engine.evaluate_kpi("k1", 1200.0)
            assert result["status"] == "met"
            assert result["progress"] == 1.0

        async def test_returns_not_met_when_below_target(self, seeded_engine: KpiEngine) -> None:
            result = await seeded_engine.evaluate_kpi("k1", 100.0)
            assert result["status"] == "not_met"

        async def test_lower_is_better_met(self, seeded_engine: KpiEngine) -> None:
            result = await seeded_engine.evaluate_kpi("k2", 50.0)
            assert result["status"] == "met"

        async def test_lower_is_better_not_met(self, seeded_engine: KpiEngine) -> None:
            result = await seeded_engine.evaluate_kpi("k2", 500.0)
            assert result["status"] == "not_met"

        async def test_returns_met_when_target_is_zero(self, seeded_engine: KpiEngine) -> None:
            tracker = GoalTracker()
            kpi = KpiDefinition(id="k_zero", name="Zero", target_value=0.0)
            tracker.register_kpi(kpi)
            engine = KpiEngine(goal_tracker=tracker)
            result = await engine.evaluate_kpi("k_zero", 100.0)
            assert result["status"] == "met"

        async def test_raises_on_unknown_kpi(self, engine: KpiEngine) -> None:
            with pytest.raises(KpiNotFoundError):
                await engine.evaluate_kpi("unknown")

    class TestGetKpiStatus:
        async def test_returns_status(self, seeded_engine: KpiEngine) -> None:
            status = await seeded_engine.get_kpi_status("k1")
            assert status["kpi_id"] == "k1"
            assert "on_track" in status
            assert "progress" in status

        async def test_raises_on_unknown(self, engine: KpiEngine) -> None:
            with pytest.raises(KpiNotFoundError):
                await engine.get_kpi_status("unknown")

    class TestGetKpiTrend:
        async def test_returns_stable_with_no_data(self, engine: KpiEngine) -> None:
            tracker = GoalTracker()
            kpi = KpiDefinition(id="k1", name="Test")
            tracker.register_kpi(kpi)
            eng = KpiEngine(goal_tracker=tracker)
            trend = await eng.get_kpi_trend("k1")
            assert trend == "stable"

        async def test_returns_trend(self, seeded_engine: KpiEngine) -> None:
            trend = await seeded_engine.get_kpi_trend("k1")
            assert isinstance(trend, str)

        async def test_raises_on_unknown(self, engine: KpiEngine) -> None:
            with pytest.raises(KpiNotFoundError):
                await engine.get_kpi_trend("unknown")

    class TestListKpis:
        async def test_returns_empty(self, engine: KpiEngine) -> None:
            kpis = await engine.list_kpis()
            assert kpis == []

        async def test_returns_registered_kpis(self, seeded_engine: KpiEngine) -> None:
            kpis = await seeded_engine.list_kpis()
            assert len(kpis) == 2

        async def test_returns_kpi_definitions(self, seeded_engine: KpiEngine) -> None:
            kpis = await seeded_engine.list_kpis()
            assert all(isinstance(k, KpiDefinition) for k in kpis)

    class TestConstruction:
        def test_default_construction(self) -> None:
            engine = KpiEngine()
            assert isinstance(engine, KpiEngine)

        def test_with_deps(self) -> None:
            tracker = GoalTracker()
            svc = AnalyticsService()
            trends = TrendAnalyzer(analytics_service=svc)
            engine = KpiEngine(analytics_service=svc, goal_tracker=tracker, trend_analyzer=trends)
            assert engine is not None
