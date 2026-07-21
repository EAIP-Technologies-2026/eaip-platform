"""WorkflowAnalyticsService — metrics, throughput, bottlenecks, trends, reporting."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now
from eaip.workflow_analytics.exceptions import (
    WorkflowAnalyticsDataNotFoundError,
    WorkflowAnalyticsQueryError,
)
from eaip.workflow_analytics.models import (
    AnalyticsPeriod,
    BottleneckReport,
    PerformanceTrend,
    ThroughputAnalysis,
    WorkflowAnalyticsConfig,
    WorkflowAnalyticsReport,
    WorkflowMetrics,
)


class WorkflowAnalyticsService:
    """Central service for collecting and analyzing workflow analytics."""

    def __init__(self, config: WorkflowAnalyticsConfig | None = None) -> None:
        self._config = config or WorkflowAnalyticsConfig()
        self._metrics_store: dict[str, list[WorkflowMetrics]] = defaultdict(list)
        self._reports: dict[str, WorkflowAnalyticsReport] = {}
        self._log = get_logger("eaip.workflow_analytics.service")

    @property
    def config(self) -> WorkflowAnalyticsConfig:
        return self._config

    async def record_metrics(self, metrics: WorkflowMetrics) -> WorkflowMetrics:
        """Record workflow metrics."""
        self._metrics_store[metrics.workflow_id].append(metrics)
        self._trim_old_metrics(metrics.workflow_id)
        self._log.info(
            "workflow_analytics.metrics.recorded",
            workflow_id=metrics.workflow_id,
            total_executions=metrics.total_executions,
        )
        return metrics

    async def get_metrics(
        self, workflow_id: str, period: AnalyticsPeriod = AnalyticsPeriod.LAST_24H
    ) -> list[WorkflowMetrics]:
        """Get recorded metrics for a workflow, optionally filtered by period."""
        all_metrics = self._metrics_store.get(workflow_id, [])
        if not all_metrics:
            raise WorkflowAnalyticsDataNotFoundError(workflow_id)

        cutoff = _period_to_cutoff(period)
        return [m for m in all_metrics if m.collected_at >= cutoff]

    async def analyze_throughput(
        self, workflow_id: str, period: AnalyticsPeriod = AnalyticsPeriod.LAST_24H
    ) -> ThroughputAnalysis:
        """Analyze workflow throughput for a given period."""
        metrics_list = await self.get_metrics(workflow_id, period)
        if not metrics_list:
            total = 0
            peak_hour = ""
            peak_count = 0
        else:
            total = sum(m.total_executions for m in metrics_list)
            hour_counts: dict[str, int] = {}
            for m in metrics_list:
                hour_key = m.collected_at.strftime("%Y-%m-%d %H:00")
                hour_counts[hour_key] = hour_counts.get(hour_key, 0) + m.total_executions
            peak_hour = max(hour_counts, key=lambda h: hour_counts[h]) if hour_counts else ""
            peak_count = hour_counts.get(peak_hour, 0)

        period_hours = _period_to_hours(period)
        executions_per_hour = round(total / period_hours, 2) if period_hours > 0 else 0.0
        throughput_trend = "increasing" if executions_per_hour > 10 else "stable"

        return ThroughputAnalysis(
            workflow_id=workflow_id,
            period=period,
            total_executions=total,
            executions_per_hour=executions_per_hour,
            peak_hour=peak_hour,
            peak_executions=peak_count,
            throughput_trend=throughput_trend,
        )

    async def detect_bottlenecks(
        self, workflow_id: str, period: AnalyticsPeriod = AnalyticsPeriod.LAST_24H
    ) -> tuple[BottleneckReport, ...]:
        """Detect bottlenecks in workflow execution."""
        metrics_list = await self.get_metrics(workflow_id, period)
        bottlenecks: list[BottleneckReport] = []

        for m in metrics_list:
            if m.failed > 0 and m.total_executions > 0:
                failure_rate = m.failed / m.total_executions
                if failure_rate > 0.2:
                    bottlenecks.append(
                        BottleneckReport(
                            workflow_id=workflow_id,
                            bottleneck_type="high_failure_rate",
                            description=f"Failure rate {failure_rate:.0%} exceeds 20% threshold",
                            affected_steps=(),
                            severity="high",
                            avg_wait_time_seconds=m.avg_duration_seconds,
                            suggested_action="Investigate recent failures and review error logs",
                        )
                    )

            if m.avg_duration_seconds > self._config.sla_threshold_seconds:
                bottlenecks.append(
                    BottleneckReport(
                        workflow_id=workflow_id,
                        bottleneck_type="sla_violation",
                        description=(
                            f"Average duration {m.avg_duration_seconds:.1f}s exceeds SLA threshold"
                        ),
                        affected_steps=(),
                        severity="medium",
                        avg_wait_time_seconds=m.avg_duration_seconds,
                        suggested_action=(
                            "Review workflow step durations and optimize long-running steps"
                        ),
                    )
                )

        return tuple(bottlenecks[: self._config.max_bottlenecks_per_report])

    async def compute_trends(
        self, workflow_id: str, period: AnalyticsPeriod = AnalyticsPeriod.LAST_7D
    ) -> tuple[PerformanceTrend, ...]:
        """Compute performance trends for a workflow."""
        metrics_list = await self.get_metrics(workflow_id, period)
        if len(metrics_list) < 2:
            return ()

        half = len(metrics_list) // 2
        first_half = metrics_list[:half]
        second_half = metrics_list[half:]

        baseline_avg = sum(m.avg_duration_seconds for m in first_half) / len(first_half)
        current_avg = sum(m.avg_duration_seconds for m in second_half) / len(second_half)
        change_pct = (
            ((current_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0.0
        )

        if change_pct > 5:
            direction = "degrading"
        elif change_pct < -5:
            direction = "improving"
        else:
            direction = "stable"

        trend = PerformanceTrend(
            workflow_id=workflow_id,
            metric_name="avg_duration_seconds",
            direction=direction,
            change_percent=round(change_pct, 2),
            confidence=0.8,
            baseline_avg=round(baseline_avg, 2),
            current_avg=round(current_avg, 2),
            data_points=len(metrics_list),
        )
        return (trend,)

    async def compute_sla_compliance(
        self, workflow_id: str, period: AnalyticsPeriod = AnalyticsPeriod.LAST_24H
    ) -> float:
        """Compute SLA compliance percentage for a workflow."""
        metrics_list = await self.get_metrics(workflow_id, period)
        if not metrics_list:
            return 100.0

        compliant = sum(
            1 for m in metrics_list if m.avg_duration_seconds <= self._config.sla_threshold_seconds
        )
        return round(compliant / len(metrics_list) * 100, 2)

    async def generate_report(
        self, workflow_id: str, period: AnalyticsPeriod = AnalyticsPeriod.LAST_24H
    ) -> WorkflowAnalyticsReport:
        """Generate a comprehensive workflow analytics report."""
        try:
            metrics_list = await self.get_metrics(workflow_id, period)
        except WorkflowAnalyticsDataNotFoundError:
            raise WorkflowAnalyticsQueryError(
                f"no data available to generate report for workflow {workflow_id!r}"
            ) from None

        latest_metrics = metrics_list[-1] if metrics_list else None

        throughput = await self.analyze_throughput(workflow_id, period)
        bottlenecks = await self.detect_bottlenecks(workflow_id, period)
        trends = await self.compute_trends(workflow_id, period)
        sla_pct = await self.compute_sla_compliance(workflow_id, period)

        report = WorkflowAnalyticsReport(
            id=f"war_{utc_now().timestamp():.0f}",
            workflow_id=workflow_id,
            period=period,
            metrics=latest_metrics,
            throughput=throughput,
            bottlenecks=bottlenecks,
            trends=trends,
            sla_compliance_pct=sla_pct,
        )
        self._reports[report.id] = report
        self._log.info(
            "workflow_analytics.report.generated",
            report_id=report.id,
            workflow_id=workflow_id,
        )
        return report

    async def get_report(self, report_id: str) -> WorkflowAnalyticsReport:
        """Get a previously generated report by ID."""
        report = self._reports.get(report_id)
        if report is None:
            raise WorkflowAnalyticsDataNotFoundError(report_id)
        return report

    async def list_reports(self, workflow_id: str | None = None) -> list[WorkflowAnalyticsReport]:
        """List all generated reports, optionally filtered by workflow."""
        reports = list(self._reports.values())
        if workflow_id:
            reports = [r for r in reports if r.workflow_id == workflow_id]
        return sorted(reports, key=lambda r: r.generated_at, reverse=True)

    def _trim_old_metrics(self, workflow_id: str) -> None:
        """Remove metrics older than the retention period."""
        points = self._metrics_store.get(workflow_id, [])
        cutoff = utc_now() - timedelta(days=self._config.retention_days)
        self._metrics_store[workflow_id] = [p for p in points if p.collected_at >= cutoff]

    async def update_config(self, config: WorkflowAnalyticsConfig) -> WorkflowAnalyticsConfig:
        """Update the service configuration."""
        self._config = config
        self._log.info("workflow_analytics.config.updated")
        return self._config


def _period_to_cutoff(period: AnalyticsPeriod) -> datetime:
    now = utc_now()
    mapping = {
        AnalyticsPeriod.LAST_HOUR: now - timedelta(hours=1),
        AnalyticsPeriod.LAST_24H: now - timedelta(hours=24),
        AnalyticsPeriod.LAST_7D: now - timedelta(days=7),
        AnalyticsPeriod.LAST_30D: now - timedelta(days=30),
        AnalyticsPeriod.CUSTOM: datetime.min.replace(tzinfo=now.tzinfo),
    }
    return mapping.get(period, now - timedelta(hours=24))


def _period_to_hours(period: AnalyticsPeriod) -> float:
    mapping = {
        AnalyticsPeriod.LAST_HOUR: 1,
        AnalyticsPeriod.LAST_24H: 24,
        AnalyticsPeriod.LAST_7D: 168,
        AnalyticsPeriod.LAST_30D: 720,
        AnalyticsPeriod.CUSTOM: 24,
    }
    return mapping.get(period, 24)


__all__ = ["WorkflowAnalyticsService"]
