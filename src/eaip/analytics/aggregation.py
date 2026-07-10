"""AggregationEngine — time-series aggregation, rollups, derived metrics, percentiles."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from eaip.analytics.exceptions import AnalyticsQueryError, MetricNotFoundError
from eaip.analytics.models import AggregationType, MetricPoint, MetricType, TimeSeriesPoint, TimeSeriesResult
from eaip.analytics.service import AnalyticsService
from eaip.logging.context import get_logger


class AggregationEngine:
    """Performs aggregation, rollup, derived metric computation, and percentile calculations."""

    def __init__(self, analytics_service: AnalyticsService | None = None) -> None:
        self._analytics = analytics_service or AnalyticsService()
        self._log = get_logger("eaip.analytics.aggregation")

    async def aggregate(
        self,
        metric_id: str,
        aggregation: AggregationType,
        time_range: tuple[datetime, datetime],
        interval: float = 60.0,
    ) -> TimeSeriesResult:
        """Aggregate a metric's time series using the specified aggregation function."""
        return await self._analytics.query_time_series(metric_id, time_range[0], time_range[1], interval, aggregation)

    async def rollup(self, metric_ids: list[str], aggregation: AggregationType) -> dict[str, float]:
        """Roll up multiple metrics into a single summary value per metric."""
        now = datetime.now(timezone.utc)
        start = datetime(1970, 1, 1, tzinfo=timezone.utc)
        end = now

        results: dict[str, float] = {}
        for mid in metric_ids:
            try:
                result = await self._analytics.query_time_series(mid, start, end, interval=86400.0, aggregation=aggregation)
                if result.points:
                    results[mid] = result.points[-1].value
                else:
                    results[mid] = 0.0
            except MetricNotFoundError:
                results[mid] = 0.0

        return results

    async def compute_derived(
        self,
        expression: str,
        source_metrics: dict[str, str],
        time_range: tuple[datetime, datetime],
    ) -> list[dict[str, Any]]:
        """Compute a derived metric from source metrics using a simple expression."""
        if expression not in ("sum", "avg", "diff", "ratio", "product"):
            raise AnalyticsQueryError(f"unsupported expression: {expression}")

        series_data: dict[str, list[TimeSeriesPoint]] = {}
        for alias, mid in source_metrics.items():
            try:
                result = await self._analytics.query_time_series(mid, time_range[0], time_range[1], aggregation=AggregationType.AVG)
                series_data[alias] = list(result.points)
            except MetricNotFoundError:
                series_data[alias] = []

        min_len = min(len(v) for v in series_data.values()) if series_data else 0
        if min_len == 0:
            return []

        derived: list[dict[str, Any]] = []
        for i in range(min_len):
            ts = list(series_data.values())[0][i].timestamp
            vals = {alias: series_data[alias][i].value for alias in source_metrics}

            if expression == "sum":
                result_val = sum(vals.values())
            elif expression == "avg":
                result_val = sum(vals.values()) / len(vals)
            elif expression == "diff":
                keys = list(vals.keys())
                result_val = vals[keys[0]] - vals[keys[1]] if len(keys) >= 2 else 0.0
            elif expression == "ratio":
                keys = list(vals.keys())
                denominator = max(vals[keys[1]], 0.001) if len(keys) >= 2 else 1.0
                result_val = vals[keys[0]] / denominator
            elif expression == "product":
                result_val = math.prod(vals.values())
            else:
                result_val = 0.0

            derived.append({
                "timestamp": ts,
                "value": round(result_val, 6),
                "expression": expression,
                "inputs": vals,
            })

        return derived

    async def compute_percentile(
        self,
        metric_id: str,
        percentile: float,
        time_range: tuple[datetime, datetime],
    ) -> dict[str, Any]:
        """Compute a percentile value for a metric over a time range."""
        if percentile < 0 or percentile > 100:
            raise AnalyticsQueryError("percentile must be between 0 and 100")

        try:
            result = await self._analytics.query_time_series(metric_id, time_range[0], time_range[1], aggregation=AggregationType.AVG)
        except MetricNotFoundError:
            return {"metric_id": metric_id, "percentile": percentile, "value": 0.0, "count": 0}
        points = result.points

        if not points:
            return {"metric_id": metric_id, "percentile": percentile, "value": 0.0, "count": 0}

        values = sorted(p.value for p in points)
        n = len(values)
        k = (percentile / 100.0) * (n - 1)
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            p_val = values[int(k)]
        else:
            d0 = values[f] * (c - k)
            d1 = values[c] * (k - f)
            p_val = d0 + d1

        return {
            "metric_id": metric_id,
            "percentile": percentile,
            "value": round(p_val, 6),
            "count": n,
            "min": values[0],
            "max": values[-1],
        }


__all__ = ["AggregationEngine"]
