"""AnalyticsService — metric recording, time-series queries, and report generation."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from eaip.analytics.exceptions import MetricNotFoundError
from eaip.analytics.models import (
    AggregationType,
    AnalyticsConfig,
    AnalyticsReport,
    MetricDefinition,
    MetricPoint,
    TimeSeriesPoint,
    TimeSeriesResult,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AnalyticsService:
    """Central service for recording and querying analytical metrics."""

    def __init__(self, config: AnalyticsConfig | None = None) -> None:
        self._config = config or AnalyticsConfig()
        self._metrics: dict[str, MetricDefinition] = {}
        self._points: dict[str, list[MetricPoint]] = defaultdict(list)
        self._log = get_logger("eaip.analytics.service")

    @property
    def config(self) -> AnalyticsConfig:
        return self._config

    async def register_metric(self, definition: MetricDefinition) -> MetricDefinition:
        """Register a new metric definition."""
        self._metrics[definition.id] = definition
        self._log.info("analytics.metric.registered", metric_id=definition.id, name=definition.name)
        return definition

    async def get_metric(self, metric_id: str) -> MetricDefinition:
        """Get a metric definition by ID."""
        definition = self._metrics.get(metric_id)
        if definition is None:
            raise MetricNotFoundError(metric_id)
        return definition

    async def list_metrics(self, tags: tuple[str, ...] | None = None) -> list[MetricDefinition]:
        """List all registered metric definitions, optionally filtered by tags."""
        result = list(self._metrics.values())
        if tags:
            result = [m for m in result if all(t in m.tags for t in tags)]
        return result

    async def record_metric(
        self, metric_id: str, value: float, tags: dict[str, str] | None = None
    ) -> MetricPoint:
        """Record a metric data point."""
        if metric_id not in self._metrics:
            raise MetricNotFoundError(metric_id)

        definition = self._metrics[metric_id]
        if not definition.enabled:
            self._log.warning("analytics.metric.disabled", metric_id=metric_id)
            return MetricPoint(
                metric_id=metric_id, timestamp=utc_now(), value=value, tags=tags or {}
            )

        point = MetricPoint(
            metric_id=metric_id,
            timestamp=utc_now(),
            value=value,
            tags=tags or {},
        )
        self._points[metric_id].append(point)

        self._trim_old_points(metric_id)
        self._log.info("analytics.metric.recorded", metric_id=metric_id, value=value)
        return point

    async def query_time_series(
        self,
        metric_id: str,
        start: datetime,
        end: datetime,
        interval: float = 60.0,
        aggregation: AggregationType = AggregationType.SUM,
    ) -> TimeSeriesResult:
        """Query time series data for a metric within a time range."""
        if metric_id not in self._metrics:
            raise MetricNotFoundError(metric_id)

        points = [p for p in self._points.get(metric_id, []) if start <= p.timestamp <= end]
        if not points:
            return TimeSeriesResult(
                metric_id=metric_id,
                points=(),
                aggregation=aggregation,
                start_time=start,
                end_time=end,
                interval_seconds=interval,
            )

        buckets: dict[int, list[float]] = {}
        interval_ms = int(interval * 1000)
        for p in points:
            bucket_key = int(p.timestamp.timestamp() * 1000) // interval_ms
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            buckets[bucket_key].append(p.value)

        tspans: list[TimeSeriesPoint] = []
        for bucket_key in sorted(buckets):
            vals = buckets[bucket_key]
            bucket_ts = datetime.fromtimestamp(bucket_key * interval_ms / 1000)
            label = aggregation
            if aggregation == AggregationType.SUM:
                agg_val = sum(vals)
            elif aggregation == AggregationType.AVG:
                agg_val = sum(vals) / len(vals)
            elif aggregation == AggregationType.MIN:
                agg_val = min(vals)
            elif aggregation == AggregationType.MAX:
                agg_val = max(vals)
            elif aggregation == AggregationType.COUNT:
                agg_val = float(len(vals))
            elif aggregation == AggregationType.LATEST:
                agg_val = vals[-1]
            else:
                agg_val = sum(vals)

            tspans.append(
                TimeSeriesPoint(timestamp=bucket_ts, value=round(agg_val, 6), label=str(label))
            )

        return TimeSeriesResult(
            metric_id=metric_id,
            points=tuple(tspans),
            aggregation=aggregation,
            start_time=start,
            end_time=end,
            interval_seconds=interval,
        )

    async def generate_report(
        self,
        metric_ids: list[str],
        time_range: tuple[datetime, datetime],
        interval: float = 60.0,
    ) -> AnalyticsReport:
        """Generate an analytics report for the given metrics and time range."""
        results: dict[str, TimeSeriesResult] = {}
        for mid in metric_ids:
            if mid in self._metrics:
                results[mid] = await self.query_time_series(
                    mid, time_range[0], time_range[1], interval
                )

        report = AnalyticsReport(
            id=f"report_{utc_now().timestamp():.0f}",
            name=f"Report ({len(metric_ids)} metrics)",
            description=f"Analytics report covering {len(metric_ids)} metrics",
            metric_ids=tuple(metric_ids),
            time_range=time_range,
            interval=interval,
            results=results,
        )
        self._log.info(
            "analytics.report.generated", report_id=report.id, metric_count=len(metric_ids)
        )
        return report

    def _trim_old_points(self, metric_id: str) -> None:
        """Remove data points older than the retention period."""
        points = self._points.get(metric_id, [])
        if len(points) <= self._config.max_data_points:
            return
        cutoff = utc_now() - timedelta(days=self._config.retention_days)
        self._points[metric_id] = [p for p in points if p.timestamp >= cutoff]


__all__ = ["AnalyticsService"]
