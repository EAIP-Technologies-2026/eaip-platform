"""Tests for GoalTracker."""

from __future__ import annotations

import pytest

from eaip.goals.exceptions import KpiNotFoundError
from eaip.goals.models import KpiDefinition, KpiDirection
from eaip.goals.tracker import GoalTracker


class TestGoalTracker:
    @pytest.fixture
    def tracker(self) -> GoalTracker:
        return GoalTracker()

    @pytest.fixture
    def setup_kpis(self, tracker: GoalTracker) -> None:
        tracker.register_kpi(
            KpiDefinition(id="k1", name="Revenue", target_value=1000.0, current_value=0.0),
        )
        tracker.register_kpi(
            KpiDefinition(
                id="k2",
                name="Latency",
                target_value=100.0,
                current_value=200.0,
                direction=KpiDirection.LOWER_IS_BETTER,
            ),
        )

    async def test_record_kpi(self, tracker: GoalTracker, setup_kpis: None) -> None:
        previous = await tracker.record_kpi("k1", 500.0)
        assert previous == 0.0

    async def test_record_kpi_not_found(self, tracker: GoalTracker) -> None:
        with pytest.raises(KpiNotFoundError):
            await tracker.record_kpi("nonexistent", 100.0)

    async def test_record_multiple_values(self, tracker: GoalTracker, setup_kpis: None) -> None:
        await tracker.record_kpi("k1", 200.0)
        await tracker.record_kpi("k1", 500.0)
        await tracker.record_kpi("k1", 800.0)
        history = await tracker.get_kpi_history("k1")
        assert len(history) == 3
        assert history[0]["value"] == 200.0
        assert history[-1]["value"] == 800.0

    async def test_get_kpi_history_limit(self, tracker: GoalTracker, setup_kpis: None) -> None:
        for i in range(10):
            await tracker.record_kpi("k1", float(i * 100))
        history = await tracker.get_kpi_history("k1", limit=3)
        assert len(history) == 3
        assert history[0]["value"] == 700.0
        assert history[-1]["value"] == 900.0

    async def test_get_kpi_history_not_found(self, tracker: GoalTracker) -> None:
        with pytest.raises(KpiNotFoundError):
            await tracker.get_kpi_history("nonexistent")

    async def test_calculate_trend_increasing(self, tracker: GoalTracker, setup_kpis: None) -> None:
        for v in [100, 200, 300, 400, 500]:
            await tracker.record_kpi("k1", float(v))
        trend = await tracker.calculate_kpi_trend("k1")
        assert trend == "increasing"

    async def test_calculate_trend_decreasing(self, tracker: GoalTracker, setup_kpis: None) -> None:
        for v in [500, 400, 300, 200, 100]:
            await tracker.record_kpi("k1", float(v))
        trend = await tracker.calculate_kpi_trend("k1")
        assert trend == "decreasing"

    async def test_calculate_trend_stable(self, tracker: GoalTracker, setup_kpis: None) -> None:
        await tracker.record_kpi("k1", 500.0)
        trend = await tracker.calculate_kpi_trend("k1")
        assert trend == "stable"

    async def test_calculate_trend_not_found(self, tracker: GoalTracker) -> None:
        with pytest.raises(KpiNotFoundError):
            await tracker.calculate_kpi_trend("nonexistent")

    async def test_check_kpi_status_on_track(self, tracker: GoalTracker, setup_kpis: None) -> None:
        await tracker.record_kpi("k1", 1000.0)
        status = await tracker.check_kpi_status("k1")
        assert status["on_track"] is True
        assert status["progress"] == 1.0

    async def test_check_kpi_status_lower_is_better(
        self, tracker: GoalTracker, setup_kpis: None
    ) -> None:
        await tracker.record_kpi("k2", 50.0)
        status = await tracker.check_kpi_status("k2")
        assert status["on_track"] is True

    async def test_check_kpi_status_not_found(self, tracker: GoalTracker) -> None:
        with pytest.raises(KpiNotFoundError):
            await tracker.check_kpi_status("nonexistent")
