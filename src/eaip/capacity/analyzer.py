"""CapacityAnalyzer — analyze resource usage, predict capacity needs, detect threshold breaches."""

from __future__ import annotations

from statistics import mean

from eaip.capacity.events import CapacityReportGenerated, MetricRecorded, ThresholdBreached
from eaip.capacity.exceptions import ResourceNotFoundError
from eaip.capacity.models import CapacityConfig, CapacityReport, ResourceMetric
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class CapacityAnalyzer:
    """Central service for capacity analysis and prediction."""

    def __init__(self, config: CapacityConfig | None = None) -> None:
        self._config = config or CapacityConfig()
        self._metrics: dict[str, list[ResourceMetric]] = {}
        self._reports: dict[str, CapacityReport] = {}
        self._log = get_logger("eaip.capacity.analyzer")

    @property
    def config(self) -> CapacityConfig:
        return self._config

    async def record_metric(self, metric: ResourceMetric) -> ResourceMetric:
        """Record a resource metric data point."""
        if metric.resource_id not in self._metrics:
            self._metrics[metric.resource_id] = []
        self._metrics[metric.resource_id].append(metric)

        if len(self._metrics[metric.resource_id]) > self._config.max_metrics_per_resource:
            self._metrics[metric.resource_id] = self._metrics[metric.resource_id][
                -self._config.max_metrics_per_resource :
            ]

        self._check_thresholds(metric)

        event = MetricRecorded(
            metric_id=metric.id,
            resource_id=metric.resource_id,
            metric_name=metric.metric_name,
            value=metric.value,
        )
        self._log.debug(
            "capacity.metric.recorded", resource_id=metric.resource_id, value=metric.value
        )
        return metric

    def _check_thresholds(self, metric: ResourceMetric) -> None:
        """Check if the metric value breaches any thresholds."""
        if metric.value >= self._config.threshold_critical:
            event = ThresholdBreached(
                resource_id=metric.resource_id,
                metric_name=metric.metric_name,
                current_value=metric.value,
                threshold=self._config.threshold_critical,
                threshold_type="critical",
            )
            self._log.warning(
                "capacity.threshold.critical",
                resource_id=metric.resource_id,
                value=metric.value,
            )
        elif metric.value >= self._config.threshold_warning:
            event = ThresholdBreached(
                resource_id=metric.resource_id,
                metric_name=metric.metric_name,
                current_value=metric.value,
                threshold=self._config.threshold_warning,
                threshold_type="warning",
            )
            self._log.warning(
                "capacity.threshold.warning",
                resource_id=metric.resource_id,
                value=metric.value,
            )

    async def generate_report(self, resource_id: str) -> CapacityReport:
        """Generate a capacity report for the given resource."""
        metrics = self._metrics.get(resource_id, [])
        if not metrics:
            return CapacityReport(
                id=f"rpt_{utc_now().timestamp():.0f}_{resource_id}",
                resource_id=resource_id,
                period_start=utc_now(),
                period_end=utc_now(),
                current_usage=0.0,
                predicted_usage=0.0,
                recommended_capacity=0.0,
                confidence=0.0,
            )

        current = metrics[-1].value
        values = [m.value for m in metrics]
        avg = mean(values) if values else 0.0
        predicted = avg * 1.1
        recommended = max(current, predicted) * 1.2
        confidence = min(self._config.default_confidence_threshold + 0.1, 1.0)

        report = CapacityReport(
            id=f"rpt_{utc_now().timestamp():.0f}_{resource_id}",
            resource_id=resource_id,
            period_start=metrics[0].timestamp,
            period_end=metrics[-1].timestamp,
            current_usage=current,
            predicted_usage=round(predicted, 2),
            recommended_capacity=round(recommended, 2),
            confidence=round(confidence, 2),
        )
        self._reports[report.id] = report

        event = CapacityReportGenerated(
            report_id=report.id,
            resource_id=resource_id,
            current_usage=current,
            predicted_usage=report.predicted_usage,
            recommended_capacity=report.recommended_capacity,
        )
        self._log.info("capacity.report.generated", resource_id=resource_id)
        return report

    async def get_metrics(
        self, resource_id: str, metric_name: str | None = None
    ) -> list[ResourceMetric]:
        """Retrieve metrics for a resource, optionally filtered by name."""
        metrics = self._metrics.get(resource_id, [])
        if metric_name is not None:
            return [m for m in metrics if m.metric_name == metric_name]
        return metrics

    async def get_report(self, report_id: str) -> CapacityReport:
        """Retrieve a capacity report by ID."""
        report = self._reports.get(report_id)
        if report is None:
            raise ResourceNotFoundError(f"Report '{report_id}' not found")
        return report

    async def list_reports(self, resource_id: str | None = None) -> list[CapacityReport]:
        """List capacity reports, optionally filtered by resource."""
        if resource_id is None:
            return list(self._reports.values())
        return [r for r in self._reports.values() if r.resource_id == resource_id]

    async def get_resource_ids(self) -> list[str]:
        """List all resource IDs with recorded metrics."""
        return list(self._metrics.keys())


__all__ = ["CapacityAnalyzer"]
