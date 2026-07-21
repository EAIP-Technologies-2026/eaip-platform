"""AiAnalyticsService — AI analytics metrics, reports, dashboards, anomaly detection, and exports."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from eaip.ai_analytics.exceptions import (
    AiAnalyticsConfigError,
    AiAnalyticsDashboardError,
    AiAnalyticsExportError,
    AiAnalyticsMetricError,
    AiAnalyticsQueryError,
    AiAnalyticsReportError,
    AiAnomalyDetectionError,
)
from eaip.ai_analytics.models import (
    AiAnalyticsConfig,
    AiAnalyticsDashboard,
    AiAnalyticsDashboardWidget,
    AiAnalyticsExport,
    AiAnalyticsForecast,
    AiAnalyticsInsight,
    AiAnalyticsInsightSeverity,
    AiAnalyticsMetric,
    AiAnalyticsMetricType,
    AiAnalyticsReport,
    AiAnalyticsReportPeriod,
    AiAnalyticsTrend,
    AiAnomalyDetectionResult,
    AiCostMetrics,
    AiErrorMetrics,
    AiLatencyMetrics,
    AiModelUsageMetrics,
    AiTokenUsageMetrics,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AiAnalyticsService:
    """Central service for AI-specific analytics: metrics, usage, cost, latency, and dashboards."""

    def __init__(self, config: AiAnalyticsConfig | None = None) -> None:
        self._config = config or AiAnalyticsConfig()
        self._metrics: dict[str, AiAnalyticsMetric] = {}
        self._model_usage: dict[str, list[AiModelUsageMetrics]] = defaultdict(list)
        self._token_usage: dict[str, list[AiTokenUsageMetrics]] = defaultdict(list)
        self._latency: dict[str, list[AiLatencyMetrics]] = defaultdict(list)
        self._errors: dict[str, list[AiErrorMetrics]] = defaultdict(list)
        self._costs: dict[str, list[AiCostMetrics]] = defaultdict(list)
        self._dashboards: dict[str, AiAnalyticsDashboard] = {}
        self._anomalies: list[AiAnomalyDetectionResult] = []
        self._trends: list[AiAnalyticsTrend] = []
        self._forecasts: dict[str, AiAnalyticsForecast] = {}
        self._insights: list[AiAnalyticsInsight] = []
        self._exports: dict[str, AiAnalyticsExport] = {}
        self._log = get_logger("eaip.ai_analytics.service")

    @property
    def config(self) -> AiAnalyticsConfig:
        return self._config

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    async def update_config(self, **changes: Any) -> AiAnalyticsConfig:
        """Update configuration settings."""
        if "enabled" in changes:
            self._config = AiAnalyticsConfig(**{**self._config.model_dump(), **changes})
        else:
            merged = {**self._config.model_dump(), **changes}
            self._config = AiAnalyticsConfig(**merged)
        self._log.info("ai_analytics.config.updated", changes=changes)
        return self._config

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    async def record_metric(
        self,
        metric_id: str,
        value: float,
        metric_type: AiAnalyticsMetricType = AiAnalyticsMetricType.CUSTOM,
        name: str = "",
        model_id: str = "",
        deployment_id: str = "",
        tags: dict[str, str] | None = None,
    ) -> AiAnalyticsMetric:
        """Record an AI analytics metric data point."""
        if not self._config.enabled:
            raise AiAnalyticsConfigError("AI analytics is disabled")

        metric = AiAnalyticsMetric(
            id=metric_id,
            type=metric_type,
            name=name or metric_id,
            value=value,
            tags={"model_id": model_id, "deployment_id": deployment_id, **(tags or {})},
            source=f"model/{model_id}" if model_id else "",
        )
        self._metrics[metric_id] = metric
        self._log.info("ai_analytics.metric.recorded", metric_id=metric_id, value=value)
        return metric

    async def get_metric(self, metric_id: str) -> AiAnalyticsMetric:
        """Get a recorded metric by ID."""
        metric = self._metrics.get(metric_id)
        if metric is None:
            raise AiAnalyticsMetricError(f"metric not found: {metric_id!r}")
        return metric

    async def list_metrics(
        self,
        metric_type: AiAnalyticsMetricType | None = None,
        model_id: str | None = None,
    ) -> list[AiAnalyticsMetric]:
        """List recorded metrics, optionally filtered by type or model."""
        result = list(self._metrics.values())
        if metric_type:
            result = [m for m in result if m.type == metric_type]
        if model_id:
            result = [m for m in result if m.tags.get("model_id") == model_id]
        return result

    # ------------------------------------------------------------------
    # Usage
    # ------------------------------------------------------------------

    async def report_model_usage(self, metrics: AiModelUsageMetrics) -> AiModelUsageMetrics:
        """Report AI model usage metrics."""
        key = f"{metrics.model_id}/{metrics.deployment_id}"
        self._model_usage[key].append(metrics)
        self._log.info("ai_analytics.model_usage.reported", model_id=metrics.model_id)
        return metrics

    async def report_token_usage(self, metrics: AiTokenUsageMetrics) -> AiTokenUsageMetrics:
        """Report AI token usage metrics."""
        key = f"{metrics.model_id}/{metrics.deployment_id}"
        self._token_usage[key].append(metrics)
        self._log.info("ai_analytics.token_usage.reported", model_id=metrics.model_id)
        return metrics

    async def report_latency(self, metrics: AiLatencyMetrics) -> AiLatencyMetrics:
        """Report AI latency metrics."""
        key = f"{metrics.model_id}/{metrics.deployment_id}"
        self._latency[key].append(metrics)
        self._log.info("ai_analytics.latency.reported", model_id=metrics.model_id)
        return metrics

    async def report_errors(self, metrics: AiErrorMetrics) -> AiErrorMetrics:
        """Report AI error metrics."""
        key = f"{metrics.model_id}/{metrics.deployment_id}"
        self._errors[key].append(metrics)
        self._log.info("ai_analytics.errors.reported", model_id=metrics.model_id)
        return metrics

    async def report_cost(self, metrics: AiCostMetrics) -> AiCostMetrics:
        """Report AI cost metrics."""
        key = f"{metrics.model_id}/{metrics.deployment_id}"
        self._costs[key].append(metrics)
        self._log.info("ai_analytics.cost.reported", model_id=metrics.model_id)
        return metrics

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    async def generate_report(
        self,
        model_ids: list[str],
        deployment_ids: list[str] | None = None,
        period: AiAnalyticsReportPeriod = AiAnalyticsReportPeriod.DAILY,
        time_range: tuple[datetime, datetime] | None = None,
    ) -> AiAnalyticsReport:
        """Generate an AI analytics report."""
        if not model_ids:
            raise AiAnalyticsReportError("at least one model_id is required")

        end = utc_now()
        start = time_range[0] if time_range else end - timedelta(days=1)
        end = time_range[1] if time_range else end
        deploys = deployment_ids or []

        usage: dict[str, AiModelUsageMetrics] = {}
        token: dict[str, AiTokenUsageMetrics] = {}
        latency: dict[str, AiLatencyMetrics] = {}
        error: dict[str, AiErrorMetrics] = {}
        cost: dict[str, AiCostMetrics] = {}

        for mid in model_ids:
            key = f"{mid}/"
            if key in self._model_usage:
                usages = self._model_usage[key]
                if usages:
                    usage[mid] = usages[-1]
            if key in self._token_usage:
                tokens = self._token_usage[key]
                if tokens:
                    token[mid] = tokens[-1]
            if key in self._latency:
                lats = self._latency[key]
                if lats:
                    latency[mid] = lats[-1]
            if key in self._errors:
                errs = self._errors[key]
                if errs:
                    error[mid] = errs[-1]
            if key in self._costs:
                costs = self._costs[key]
                if costs:
                    cost[mid] = costs[-1]

        report = AiAnalyticsReport(
            id=f"ai_report_{utc_now().timestamp():.0f}",
            name=f"AI Analytics Report ({len(model_ids)} models)",
            description=f"AI analytics report covering {len(model_ids)} models",
            period=period,
            time_range=(start, end),
            model_ids=tuple(model_ids),
            deployment_ids=tuple(deploys),
            usage_metrics=usage,
            token_metrics=token,
            latency_metrics=latency,
            error_metrics=error,
            cost_metrics=cost,
        )
        self._log.info("ai_analytics.report.generated", report_id=report.id)
        return report

    # ------------------------------------------------------------------
    # Dashboards
    # ------------------------------------------------------------------

    async def create_dashboard(
        self,
        name: str,
        description: str = "",
        widgets: list[AiAnalyticsDashboardWidget] | None = None,
    ) -> AiAnalyticsDashboard:
        """Create a new AI analytics dashboard."""
        dashboard_id = f"ai_dash_{utc_now().timestamp():.0f}"
        dashboard = AiAnalyticsDashboard(
            id=dashboard_id,
            name=name,
            description=description,
            widgets=tuple(widgets or []),
        )
        self._dashboards[dashboard_id] = dashboard
        self._log.info("ai_analytics.dashboard.created", dashboard_id=dashboard_id, name=name)
        return dashboard

    async def get_dashboard(self, dashboard_id: str) -> AiAnalyticsDashboard:
        """Get a dashboard by ID."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise AiAnalyticsDashboardError(f"dashboard not found: {dashboard_id!r}")
        return dashboard

    async def update_dashboard(self, dashboard_id: str, **changes: Any) -> AiAnalyticsDashboard:
        """Update an existing dashboard."""
        dashboard = await self.get_dashboard(dashboard_id)
        merged = {**dashboard.model_dump(), **changes}
        updated = AiAnalyticsDashboard(**merged)
        self._dashboards[dashboard_id] = updated
        self._log.info("ai_analytics.dashboard.updated", dashboard_id=dashboard_id)
        return updated

    async def list_dashboards(self) -> list[AiAnalyticsDashboard]:
        """List all AI analytics dashboards."""
        return list(self._dashboards.values())

    async def delete_dashboard(self, dashboard_id: str) -> None:
        """Delete a dashboard by ID."""
        if dashboard_id not in self._dashboards:
            raise AiAnalyticsDashboardError(f"dashboard not found: {dashboard_id!r}")
        del self._dashboards[dashboard_id]
        self._log.info("ai_analytics.dashboard.deleted", dashboard_id=dashboard_id)

    # ------------------------------------------------------------------
    # Anomaly Detection
    # ------------------------------------------------------------------

    async def detect_anomalies(
        self,
        metric_id: str,
        values: list[float],
        model_id: str = "",
        deployment_id: str = "",
    ) -> list[AiAnomalyDetectionResult]:
        """Detect anomalies in a series of metric values using simple statistical method."""
        if not self._config.anomaly_detection_enabled:
            raise AiAnomalyDetectionError("anomaly detection is disabled")

        if not values:
            return []

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance**0.5
        threshold = self._config.anomaly_sensitivity * std_dev

        results: list[AiAnomalyDetectionResult] = []
        for i, v in enumerate(values):
            if std_dev > 0 and abs(v - mean) > threshold:
                result = AiAnomalyDetectionResult(
                    id=f"anomaly_{utc_now().timestamp():.0f}_{i}",
                    metric_id=metric_id,
                    model_id=model_id,
                    deployment_id=deployment_id,
                    value=v,
                    expected_value=mean,
                    deviation=abs(v - mean) / (std_dev if std_dev > 0 else 1),
                    severity=(
                        AiAnalyticsInsightSeverity.CRITICAL
                        if abs(v - mean) > 3 * std_dev
                        else AiAnalyticsInsightSeverity.WARNING
                    ),
                )
                results.append(result)
                self._anomalies.append(result)

        self._log.info(
            "ai_analytics.anomaly.detected",
            metric_id=metric_id,
            anomaly_count=len(results),
        )
        return results

    async def list_anomalies(
        self,
        metric_id: str | None = None,
        model_id: str | None = None,
    ) -> list[AiAnomalyDetectionResult]:
        """List detected anomalies, optionally filtered."""
        results = list(self._anomalies)
        if metric_id:
            results = [r for r in results if r.metric_id == metric_id]
        if model_id:
            results = [r for r in results if r.model_id == model_id]
        return results

    # ------------------------------------------------------------------
    # Trends
    # ------------------------------------------------------------------

    async def compute_trend(
        self,
        metric_id: str,
        values: list[float],
        model_id: str = "",
        deployment_id: str = "",
    ) -> AiAnalyticsTrend:
        """Compute trend direction and magnitude from a series of values."""
        if not self._config.trend_detection_enabled:
            raise AiAnalyticsQueryError("trend detection is disabled")

        if len(values) < 2:
            trend = AiAnalyticsTrend(
                metric_id=metric_id,
                model_id=model_id,
                deployment_id=deployment_id,
                direction="stable",
                change_percent=0.0,
                confidence=0.0,
            )
            self._trends.append(trend)
            return trend

        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]
        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        if first_avg == 0:
            change_percent = 0.0
        else:
            change_percent = ((second_avg - first_avg) / abs(first_avg)) * 100

        if change_percent > 5:
            direction = "up"
        elif change_percent < -5:
            direction = "down"
        else:
            direction = "stable"

        confidence = min(abs(change_percent) / 100.0, 1.0)

        trend = AiAnalyticsTrend(
            metric_id=metric_id,
            model_id=model_id,
            deployment_id=deployment_id,
            direction=direction,
            change_percent=round(change_percent, 4),
            confidence=round(confidence, 4),
            period_comparison={"first_half_avg": first_avg, "second_half_avg": second_avg},
        )
        self._trends.append(trend)
        self._log.info("ai_analytics.trend.computed", metric_id=metric_id, direction=direction)
        return trend

    async def list_trends(
        self,
        metric_id: str | None = None,
        model_id: str | None = None,
    ) -> list[AiAnalyticsTrend]:
        """List computed trends, optionally filtered."""
        results = list(self._trends)
        if metric_id:
            results = [r for r in results if r.metric_id == metric_id]
        if model_id:
            results = [r for r in results if r.model_id == model_id]
        return results

    # ------------------------------------------------------------------
    # Forecasts
    # ------------------------------------------------------------------

    async def generate_forecast(
        self,
        metric_id: str,
        values: list[float],
        timestamps: list[datetime],
        model_id: str = "",
        deployment_id: str = "",
        horizon_hours: float = 24.0,
    ) -> AiAnalyticsForecast:
        """Generate a simple linear forecast based on historical values."""
        if not self._config.forecast_enabled:
            raise AiAnalyticsQueryError("forecasting is disabled")

        if len(values) < 2:
            return AiAnalyticsForecast(
                id=f"forecast_{utc_now().timestamp():.0f}",
                metric_id=metric_id,
                model_id=model_id,
                deployment_id=deployment_id,
                horizon_hours=horizon_hours,
            )

        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0
        intercept = y_mean - slope * x_mean

        last_ts = timestamps[-1]
        interval = (timestamps[-1] - timestamps[0]).total_seconds() / max(n - 1, 1)
        forecast_count = max(1, int(horizon_hours * 3600 / interval))

        points: list[tuple[datetime, float]] = []
        upper: list[float] = []
        lower: list[float] = []

        for i in range(forecast_count):
            x = n + i
            y = slope * x + intercept
            ts = last_ts + timedelta(seconds=interval * (i + 1))
            points.append((ts, round(y, 6)))
            upper.append(round(y * 1.1, 6))
            lower.append(round(y * 0.9, 6))

        forecast = AiAnalyticsForecast(
            id=f"forecast_{utc_now().timestamp():.0f}",
            metric_id=metric_id,
            model_id=model_id,
            deployment_id=deployment_id,
            forecast_points=tuple(points),
            confidence_upper=tuple(upper),
            confidence_lower=tuple(lower),
            horizon_hours=horizon_hours,
        )
        self._forecasts[forecast.id] = forecast
        self._log.info("ai_analytics.forecast.generated", metric_id=metric_id)
        return forecast

    async def get_forecast(self, forecast_id: str) -> AiAnalyticsForecast:
        """Get a forecast by ID."""
        forecast = self._forecasts.get(forecast_id)
        if forecast is None:
            raise AiAnalyticsQueryError(f"forecast not found: {forecast_id!r}")
        return forecast

    # ------------------------------------------------------------------
    # Insights
    # ------------------------------------------------------------------

    async def generate_insight(
        self,
        title: str,
        description: str = "",
        severity: AiAnalyticsInsightSeverity = AiAnalyticsInsightSeverity.INFO,
        metric_ids: list[str] | None = None,
        model_ids: list[str] | None = None,
        recommendation: str = "",
    ) -> AiAnalyticsInsight:
        """Generate an actionable insight from AI analytics data."""
        insight = AiAnalyticsInsight(
            id=f"insight_{utc_now().timestamp():.0f}",
            title=title,
            description=description,
            severity=severity,
            metric_ids=tuple(metric_ids or []),
            model_ids=tuple(model_ids or []),
            recommendation=recommendation,
        )
        self._insights.append(insight)
        self._log.info("ai_analytics.insight.generated", title=title)
        return insight

    async def list_insights(
        self,
        severity: AiAnalyticsInsightSeverity | None = None,
        model_id: str | None = None,
    ) -> list[AiAnalyticsInsight]:
        """List generated insights, optionally filtered."""
        results = list(self._insights)
        if severity:
            results = [r for r in results if r.severity == severity]
        if model_id:
            results = [r for r in results if model_id in r.model_ids]
        return results

    # ------------------------------------------------------------------
    # Exports
    # ------------------------------------------------------------------

    async def export_report(
        self,
        report_id: str,
        format: str = "json",
        destination: str = "",
    ) -> AiAnalyticsExport:
        """Export an AI analytics report."""
        if not self._config.export_enabled:
            raise AiAnalyticsExportError("export is disabled")

        export = AiAnalyticsExport(
            id=f"export_{utc_now().timestamp():.0f}",
            report_id=report_id,
            format=format,
            destination=destination,
        )
        self._exports[export.id] = export
        self._log.info("ai_analytics.export.completed", export_id=export.id)
        return export

    async def get_export(self, export_id: str) -> AiAnalyticsExport:
        """Get an export by ID."""
        export = self._exports.get(export_id)
        if export is None:
            raise AiAnalyticsExportError(f"export not found: {export_id!r}")
        return export

    async def list_exports(self) -> list[AiAnalyticsExport]:
        """List all exports."""
        return list(self._exports.values())


__all__ = ["AiAnalyticsService"]
