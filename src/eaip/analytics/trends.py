"""TrendAnalyzer — trend detection, anomaly detection, forecasting, period comparison, seasonality."""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Any

from eaip.analytics.models import AggregationType, TrendAnalysis, TrendDirection
from eaip.analytics.service import AnalyticsService
from eaip.logging.context import get_logger


class TrendAnalyzer:
    """Analyzes trends, detects anomalies, and computes forecasts for metrics."""

    def __init__(self, analytics_service: AnalyticsService | None = None) -> None:
        self._analytics = analytics_service or AnalyticsService()
        self._log = get_logger("eaip.analytics.trends")

    async def analyze_trend(
        self, metric_id: str, time_range: tuple[datetime, datetime]
    ) -> TrendAnalysis:
        """Analyze the trend direction for a metric over a time range."""
        result = await self._analytics.query_time_series(
            metric_id, time_range[0], time_range[1], aggregation=AggregationType.AVG
        )
        points = result.points

        if len(points) < 2:
            return TrendAnalysis(
                metric_id=metric_id,
                direction=TrendDirection.STABLE,
                change_percent=0.0,
                confidence=0.0,
            )

        values = [p.value for p in points]
        first_val = values[0]
        last_val = values[-1]
        tolerance = 0.01 * max(abs(first_val), abs(last_val), 1.0)
        change = last_val - first_val
        change_percent = (change / max(abs(first_val), 0.001)) * 100.0

        if abs(change) <= tolerance:
            direction = TrendDirection.STABLE
        elif change > 0:
            direction = TrendDirection.UP
        else:
            direction = TrendDirection.DOWN

        # Simple volatility check
        if len(values) > 3:
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
            mean_val = statistics.mean(values)
            cv = std_dev / max(abs(mean_val), 0.001)
            if cv > 1.0:
                direction = TrendDirection.VOLATILE

        confidence = min(abs(change_percent) / 100.0, 1.0) if change_percent != 0 else 0.5

        return TrendAnalysis(
            metric_id=metric_id,
            direction=direction,
            change_percent=round(change_percent, 4),
            confidence=round(confidence, 4),
        )

    async def detect_anomalies(
        self, metric_id: str, time_range: tuple[datetime, datetime], sensitivity: float = 2.0
    ) -> list[dict[str, Any]]:
        """Detect anomalies in a metric's time series using standard deviation."""
        result = await self._analytics.query_time_series(
            metric_id, time_range[0], time_range[1], aggregation=AggregationType.AVG
        )
        points = result.points

        if len(points) < 3:
            return []

        values = [p.value for p in points]
        mean_val = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0

        anomalies: list[dict[str, Any]] = []
        threshold = sensitivity * std_dev
        for p in points:
            if std_dev > 0 and abs(p.value - mean_val) > threshold:
                anomalies.append(
                    {
                        "timestamp": p.timestamp,
                        "value": p.value,
                        "expected": round(mean_val, 6),
                        "deviation": round(abs(p.value - mean_val), 6),
                        "severity": "high" if abs(p.value - mean_val) > 3 * std_dev else "medium",
                    }
                )

        return anomalies

    async def forecast(
        self, metric_id: str, time_range: tuple[datetime, datetime], horizon: int = 5
    ) -> list[dict[str, Any]]:
        """Generate a simple forecast based on linear regression."""
        result = await self._analytics.query_time_series(
            metric_id, time_range[0], time_range[1], aggregation=AggregationType.AVG
        )
        points = result.points

        if len(points) < 2:
            return []

        values = [p.value for p in points]
        n = len(values)
        x_mean = (n - 1) / 2.0
        y_mean = statistics.mean(values)

        numerator = sum(i * values[i] for i in range(n)) - n * x_mean * y_mean
        denominator = sum(i * i for i in range(n)) - n * x_mean * x_mean
        slope = numerator / denominator if denominator != 0 else 0.0
        intercept = y_mean - slope * x_mean

        forecasts: list[dict[str, Any]] = []
        last_ts = points[-1].timestamp
        for i in range(1, horizon + 1):
            pred_ts = last_ts + timedelta(seconds=result.interval_seconds * i)
            pred_val = intercept + slope * (n - 1 + i)
            forecasts.append(
                {
                    "timestamp": pred_ts,
                    "forecast_value": round(pred_val, 6),
                    "confidence_upper": round(pred_val * 1.1, 6),
                    "confidence_lower": round(pred_val * 0.9, 6),
                }
            )

        return forecasts

    async def compare_periods(
        self,
        metric_id: str,
        period1: tuple[datetime, datetime],
        period2: tuple[datetime, datetime],
    ) -> dict[str, Any]:
        """Compare two time periods for a metric."""
        r1 = await self._analytics.query_time_series(
            metric_id, period1[0], period1[1], aggregation=AggregationType.AVG
        )
        r2 = await self._analytics.query_time_series(
            metric_id, period2[0], period2[1], aggregation=AggregationType.AVG
        )

        v1 = statistics.mean([p.value for p in r1.points]) if r1.points else 0.0
        v2 = statistics.mean([p.value for p in r2.points]) if r2.points else 0.0

        change = v2 - v1
        change_pct = (change / max(abs(v1), 0.001)) * 100.0

        return {
            "metric_id": metric_id,
            "period1_avg": round(v1, 6),
            "period2_avg": round(v2, 6),
            "change": round(change, 6),
            "change_percent": round(change_pct, 4),
            "period1_points": len(r1.points),
            "period2_points": len(r2.points),
        }

    async def get_seasonality(
        self, metric_id: str, time_range: tuple[datetime, datetime]
    ) -> dict[str, Any]:
        """Detect seasonality patterns using autocorrelation at lag intervals."""
        result = await self._analytics.query_time_series(
            metric_id, time_range[0], time_range[1], aggregation=AggregationType.AVG
        )
        points = result.points

        if len(points) < 4:
            return {"metric_id": metric_id, "seasonality_detected": False, "patterns": []}

        values = [p.value for p in points]
        n = len(values)
        mean_val = statistics.mean(values)

        # Simple autocorrelation at various lags
        patterns: list[dict[str, Any]] = []
        for lag in range(1, min(n // 2, 12) + 1):
            if lag >= n:
                break
            numerator = sum(
                (values[i] - mean_val) * (values[i + lag] - mean_val) for i in range(n - lag)
            )
            denominator = sum((v - mean_val) ** 2 for v in values)
            if denominator != 0:
                acf = numerator / denominator
                if abs(acf) > 0.5:
                    patterns.append(
                        {
                            "lag": lag,
                            "correlation": round(acf, 4),
                            "interval_seconds": result.interval_seconds * lag,
                        }
                    )

        return {
            "metric_id": metric_id,
            "seasonality_detected": len(patterns) > 0,
            "patterns": patterns,
        }


__all__ = ["TrendAnalyzer"]
