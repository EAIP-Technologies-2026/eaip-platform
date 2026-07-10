"""Tests for TrendAnalyzer."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from eaip.analytics.models import AggregationType, MetricDefinition, MetricPoint, MetricType, TrendDirection
from eaip.analytics.service import AnalyticsService
from eaip.analytics.trends import TrendAnalyzer


class TestTrendAnalyzer:
    @pytest.fixture
    async def seeded_analyzer(self) -> TrendAnalyzer:
        svc = AnalyticsService()
        m = MetricDefinition(id="m1", name="Requests", type=MetricType.COUNTER, unit="count")
        await svc.register_metric(m)
        now = datetime.now(timezone.utc)
        for i in range(10):
            point_ts = now - timedelta(minutes=(10 - i) * 5)
            svc._points["m1"].append(
                MetricPoint(metric_id="m1", timestamp=point_ts, value=float(i * 10), tags={"env": "test"}),
            )
        return TrendAnalyzer(analytics_service=svc)

    class TestAnalyzeTrend:
        async def test_returns_trend_analysis(self, seeded_analyzer: TrendAnalyzer) -> None:
            now = datetime.now(timezone.utc)
            start = now - timedelta(hours=2)
            result = await seeded_analyzer.analyze_trend("m1", (start, now))
            assert result.metric_id == "m1"
            assert isinstance(result.direction, TrendDirection)
            assert isinstance(result.change_percent, float)

        async def test_returns_stable_for_single_point(self) -> None:
            svc = AnalyticsService()
            m = MetricDefinition(id="m1", name="Test")
            await svc.register_metric(m)
            await svc.record_metric("m1", 42.0)
            analyzer = TrendAnalyzer(analytics_service=svc)
            now = datetime.now(timezone.utc)
            result = await analyzer.analyze_trend("m1", (now - timedelta(hours=1), now))
            assert result.direction is TrendDirection.STABLE

        async def test_detects_up_trend(self, seeded_analyzer: TrendAnalyzer) -> None:
            svc = AnalyticsService()
            m = MetricDefinition(id="m2", name="Growth")
            await svc.register_metric(m)
            now = datetime.now(timezone.utc)
            for i, val in enumerate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
                svc._points["m2"].append(
                    MetricPoint(metric_id="m2", timestamp=now + timedelta(minutes=i * 2), value=float(val)),
                )
            analyzer = TrendAnalyzer(analytics_service=svc)
            result = await analyzer.analyze_trend("m2", (now - timedelta(hours=1), now + timedelta(hours=1)))
            assert result.direction is TrendDirection.UP

    class TestDetectAnomalies:
        async def test_returns_empty_for_few_points(self) -> None:
            svc = AnalyticsService()
            m = MetricDefinition(id="m1", name="Test")
            await svc.register_metric(m)
            await svc.record_metric("m1", 1.0)
            await svc.record_metric("m1", 2.0)
            analyzer = TrendAnalyzer(analytics_service=svc)
            now = datetime.now(timezone.utc)
            result = await analyzer.detect_anomalies("m1", (now - timedelta(hours=1), now + timedelta(hours=1)))
            assert result == []

        async def test_detects_outliers(self, seeded_analyzer: TrendAnalyzer) -> None:
            svc = AnalyticsService()
            m = MetricDefinition(id="m3", name="WithOutlier")
            await svc.register_metric(m)
            now = datetime.now(timezone.utc)
            for i, val in enumerate([10, 12, 11, 13, 10, 11, 12, 100]):
                svc._points["m3"].append(
                    MetricPoint(metric_id="m3", timestamp=now + timedelta(minutes=i * 2), value=float(val)),
                )
            analyzer = TrendAnalyzer(analytics_service=svc)
            start = now - timedelta(hours=1)
            end = now + timedelta(hours=1)
            anomalies = await analyzer.detect_anomalies("m3", (start, end), sensitivity=1.5)
            assert len(anomalies) >= 1
            assert anomalies[0]["value"] > 50

    class TestForecast:
        async def test_returns_empty_for_few_points(self) -> None:
            svc = AnalyticsService()
            m = MetricDefinition(id="m1", name="Test")
            await svc.register_metric(m)
            await svc.record_metric("m1", 1.0)
            analyzer = TrendAnalyzer(analytics_service=svc)
            now = datetime.now(timezone.utc)
            result = await analyzer.forecast("m1", (now - timedelta(hours=1), now))
            assert result == []

        async def test_generates_forecast(self, seeded_analyzer: TrendAnalyzer) -> None:
            now = datetime.now(timezone.utc)
            start = now - timedelta(hours=2)
            result = await seeded_analyzer.forecast("m1", (start, now), horizon=3)
            assert len(result) == 3
            assert all("forecast_value" in r for r in result)

    class TestComparePeriods:
        async def test_compares_two_periods(self, seeded_analyzer: TrendAnalyzer) -> None:
            now = datetime.now(timezone.utc)
            p1 = (now - timedelta(hours=2), now - timedelta(hours=1))
            p2 = (now - timedelta(hours=1), now)
            result = await seeded_analyzer.compare_periods("m1", p1, p2)
            assert "change_percent" in result
            assert "period1_avg" in result
            assert "period2_avg" in result

        async def test_handles_empty_period(self) -> None:
            svc = AnalyticsService()
            m = MetricDefinition(id="m1", name="Test")
            await svc.register_metric(m)
            analyzer = TrendAnalyzer(analytics_service=svc)
            now = datetime.now(timezone.utc)
            result = await analyzer.compare_periods("m1", (now, now), (now, now))
            assert result["period1_avg"] == 0.0

    class TestGetSeasonality:
        async def test_returns_no_seasonality_for_few_points(self) -> None:
            svc = AnalyticsService()
            m = MetricDefinition(id="m1", name="Test")
            await svc.register_metric(m)
            await svc.record_metric("m1", 1.0)
            await svc.record_metric("m1", 2.0)
            await svc.record_metric("m1", 3.0)
            now = datetime.now(timezone.utc)
            analyzer = TrendAnalyzer(analytics_service=svc)
            result = await analyzer.get_seasonality("m1", (now - timedelta(hours=1), now))
            assert result["seasonality_detected"] is False

        async def test_detects_patterns(self, seeded_analyzer: TrendAnalyzer) -> None:
            now = datetime.now(timezone.utc)
            start = now - timedelta(hours=2)
            result = await seeded_analyzer.get_seasonality("m1", (start, now))
            assert isinstance(result["seasonality_detected"], bool)
