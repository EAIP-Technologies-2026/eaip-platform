"""Tests for AggregationEngine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.analytics.aggregation import AggregationEngine
from eaip.analytics.exceptions import AnalyticsQueryError
from eaip.analytics.models import AggregationType, MetricDefinition, MetricType
from eaip.analytics.service import AnalyticsService


class TestAggregationEngine:
    @pytest.fixture
    async def seeded_engine(self) -> AggregationEngine:
        svc = AnalyticsService()
        m1 = MetricDefinition(id="m1", name="Requests", type=MetricType.COUNTER, unit="count")
        m2 = MetricDefinition(id="m2", name="Errors", type=MetricType.COUNTER, unit="count")
        await svc.register_metric(m1)
        await svc.register_metric(m2)
        datetime.now(UTC)
        for i in range(5):
            await svc.record_metric("m1", float(i * 10))
            await svc.record_metric("m2", float(i))
        return AggregationEngine(analytics_service=svc)

    class TestAggregate:
        async def test_sum_aggregation(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.aggregate(
                "m1", AggregationType.SUM, (start, now + timedelta(hours=1)), interval=86400
            )
            assert len(result.points) >= 1
            assert result.points[0].value >= 100.0

        async def test_avg_aggregation(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.aggregate(
                "m1", AggregationType.AVG, (start, now + timedelta(hours=1)), interval=86400
            )
            assert result.points[0].value > 0

        async def test_count_aggregation(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.aggregate(
                "m1", AggregationType.COUNT, (start, now + timedelta(hours=1)), interval=86400
            )
            assert result.points[0].value == 5.0

        async def test_min_aggregation(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.aggregate(
                "m1", AggregationType.MIN, (start, now + timedelta(hours=1)), interval=86400
            )
            assert result.points[0].value == 0.0

        async def test_max_aggregation(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.aggregate(
                "m1", AggregationType.MAX, (start, now + timedelta(hours=1)), interval=86400
            )
            assert result.points[0].value == 40.0

        async def test_latest_aggregation(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.aggregate(
                "m1", AggregationType.LATEST, (start, now + timedelta(hours=1)), interval=86400
            )
            assert result.points[0].value >= 0

    class TestRollup:
        async def test_rollup_multiple_metrics(self, seeded_engine: AggregationEngine) -> None:
            result = await seeded_engine.rollup(["m1", "m2"], AggregationType.SUM)
            assert "m1" in result
            assert "m2" in result

        async def test_handles_missing_metrics(self, seeded_engine: AggregationEngine) -> None:
            result = await seeded_engine.rollup(["m1", "unknown"], AggregationType.SUM)
            assert "m1" in result
            assert "unknown" in result
            assert result["unknown"] == 0.0

    class TestComputeDerived:
        async def test_sum_expression(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.compute_derived(
                "sum",
                {"req": "m1", "err": "m2"},
                (start, now + timedelta(hours=1)),
            )
            assert len(result) > 0
            assert all(r["expression"] == "sum" for r in result)

        async def test_avg_expression(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.compute_derived(
                "avg",
                {"req": "m1", "err": "m2"},
                (start, now + timedelta(hours=1)),
            )
            assert len(result) > 0

        async def test_diff_expression(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.compute_derived(
                "diff",
                {"req": "m1", "err": "m2"},
                (start, now + timedelta(hours=1)),
            )
            assert len(result) > 0

        async def test_ratio_expression(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.compute_derived(
                "ratio",
                {"req": "m1", "err": "m2"},
                (start, now + timedelta(hours=1)),
            )
            assert len(result) > 0

        async def test_raises_on_unsupported_expression(
            self, seeded_engine: AggregationEngine
        ) -> None:
            now = datetime.now(UTC)
            with pytest.raises(AnalyticsQueryError):
                await seeded_engine.compute_derived("unsupported", {"m1": "m1"}, (now, now))

        async def test_returns_empty_with_no_data(self) -> None:
            svc = AnalyticsService()
            engine = AggregationEngine(analytics_service=svc)
            now = datetime.now(UTC)
            result = await engine.compute_derived("sum", {"m1": "unknown"}, (now, now))
            assert result == []

    class TestComputePercentile:
        async def test_p50(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.compute_percentile(
                "m1", 50.0, (start, now + timedelta(hours=1))
            )
            assert result["percentile"] == 50.0
            assert result["value"] >= 0

        async def test_p95(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.compute_percentile(
                "m1", 95.0, (start, now + timedelta(hours=1))
            )
            assert result["percentile"] == 95.0

        async def test_p99(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            start = now - timedelta(hours=1)
            result = await seeded_engine.compute_percentile(
                "m1", 99.0, (start, now + timedelta(hours=1))
            )
            assert result["percentile"] == 99.0

        async def test_raises_on_invalid_percentile(self, seeded_engine: AggregationEngine) -> None:
            now = datetime.now(UTC)
            with pytest.raises(AnalyticsQueryError):
                await seeded_engine.compute_percentile("m1", -1.0, (now, now))
            with pytest.raises(AnalyticsQueryError):
                await seeded_engine.compute_percentile("m1", 101.0, (now, now))

        async def test_returns_zero_for_empty_data(self) -> None:
            svc = AnalyticsService()
            engine = AggregationEngine(analytics_service=svc)
            now = datetime.now(UTC)
            result = await engine.compute_percentile("unknown", 50.0, (now, now))
            assert result["value"] == 0.0
            assert result["count"] == 0
