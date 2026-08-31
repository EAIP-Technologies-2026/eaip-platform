from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from eaip.ai_observability.events import (
    AiModelCallLogged,
    AiObservabilityAlertResolved,
    AiObservabilityAlertTriggered,
    AiObservabilityConfigUpdated,
    AiObservabilityDashboardCreated,
    AiObservabilityDashboardUpdated,
    AiObservabilityMetricRecorded,
    AiObservabilityReportGenerated,
    AiTraceSpanCompleted,
    AiTraceSpanFailed,
    AiTraceSpanStarted,
    AiTraceStarted,
)
from eaip.ai_observability.exceptions import (
    AiObservabilityAlertError,
    AiObservabilityConfigError,
    AiObservabilityReportError,
    AiTraceError,
)
from eaip.ai_observability.models import (
    AiModelCall,
    AiModelCallMetrics,
    AiObservabilityAlert,
    AiObservabilityAlertSeverity,
    AiObservabilityConfig,
    AiObservabilityDashboard,
    AiObservabilityMetric,
    AiObservabilityReport,
    AiTraceContext,
    AiTraceSpan,
    AiTraceSpanStatus,
    MetricType,
    SpanKind,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AiObservabilityService:
    name: str = "ai_observability.service"

    def __init__(
        self,
        config: AiObservabilityConfig | None = None,
    ) -> None:
        self._config = config or AiObservabilityConfig()
        self._traces: dict[str, list[AiTraceSpan]] = {}
        self._spans: dict[str, AiTraceSpan] = {}
        self._model_calls: dict[str, AiModelCall] = {}
        self._metrics: dict[str, list[AiObservabilityMetric]] = {}
        self._alerts: dict[str, AiObservabilityAlert] = {}
        self._dashboards: dict[str, AiObservabilityDashboard] = {}
        self._reports: dict[str, AiObservabilityReport] = {}
        self._log = get_logger("eaip.ai_observability.service")

    # -- Tracing --

    def start_trace(self, name: str, attributes: dict[str, Any] | None = None) -> str:
        trace_id = str(uuid4())
        self._traces[trace_id] = []
        AiTraceStarted(trace_id=trace_id, name=name, attributes=attributes)
        self._log.info("trace.started", trace_id=trace_id, name=name)
        return trace_id

    def start_span(
        self,
        trace_id: str,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> str:
        if trace_id not in self._traces:
            raise AiTraceError(f"Trace {trace_id!r} not found")
        span_id = str(uuid4())
        span = AiTraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            attributes=attributes or {},
        )
        self._spans[span_id] = span
        self._traces[trace_id].append(span)
        AiTraceSpanStarted(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            attributes=attributes,
        )
        self._log.info("span.started", span_id=span_id, name=name)
        return span_id

    def complete_span(
        self,
        span_id: str,
        status: AiTraceSpanStatus = AiTraceSpanStatus.OK,
        attributes: dict[str, Any] | None = None,
    ) -> AiTraceSpan:
        span = self._spans.get(span_id)
        if span is None:
            raise AiTraceError(f"Span {span_id!r} not found")
        now = utc_now()
        updated = span.model_copy(
            update={
                "status": status,
                "end_time": now,
                "attributes": {**span.attributes, **(attributes or {})},
            },
        )
        self._spans[span_id] = updated
        # Update in trace list too
        for i, s in enumerate(self._traces.get(span.trace_id, [])):
            if s.span_id == span_id:
                trace_list = list(self._traces[span.trace_id])
                trace_list[i] = updated
                self._traces[span.trace_id] = trace_list
                break
        AiTraceSpanCompleted(
            span_id=span_id,
            trace_id=span.trace_id,
            status=status,
            end_time=now,
            attributes=attributes,
        )
        self._log.info("span.completed", span_id=span_id)
        return updated

    def fail_span(
        self,
        span_id: str,
        error_message: str,
        error_type: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> AiTraceSpan:
        span = self._spans.get(span_id)
        if span is None:
            raise AiTraceError(f"Span {span_id!r} not found")
        now = utc_now()
        merged_attrs = {**span.attributes, **(attributes or {})}
        if error_type:
            merged_attrs["error.type"] = error_type
        merged_attrs["error.message"] = error_message
        updated = span.model_copy(
            update={
                "status": AiTraceSpanStatus.ERROR,
                "end_time": now,
                "attributes": merged_attrs,
            },
        )
        self._spans[span_id] = updated
        for i, s in enumerate(self._traces.get(span.trace_id, [])):
            if s.span_id == span_id:
                trace_list = list(self._traces[span.trace_id])
                trace_list[i] = updated
                self._traces[span.trace_id] = trace_list
                break
        AiTraceSpanFailed(
            span_id=span_id,
            trace_id=span.trace_id,
            error_message=error_message,
            error_type=error_type,
            attributes=attributes,
        )
        self._log.info("span.failed", span_id=span_id)
        return updated

    def get_trace_spans(self, trace_id: str) -> list[AiTraceSpan]:
        return list(self._traces.get(trace_id, []))

    def current_context(self, trace_id: str) -> AiTraceContext | None:
        spans = self._traces.get(trace_id)
        if not spans:
            return None
        last = spans[-1]
        return AiTraceContext(
            trace_id=trace_id,
            span_id=last.span_id,
            parent_span_id=last.parent_span_id,
        )

    # -- Metrics --

    def record_metric(
        self,
        name: str,
        type: MetricType,
        value: float,
        labels: dict[str, str] | None = None,
        unit: str = "",
    ) -> AiObservabilityMetric:
        metric = AiObservabilityMetric(
            name=name,
            type=type,
            value=value,
            labels=labels or {},
            unit=unit,
        )
        self._metrics.setdefault(name, []).append(metric)
        AiObservabilityMetricRecorded(
            name=name,
            type=type,
            value=value,
            labels=labels,
            unit=unit,
        )
        self._log.info("metric.recorded", name=name, value=value)
        return metric

    def get_metrics(self, name: str) -> list[AiObservabilityMetric]:
        return list(self._metrics.get(name, []))

    # -- Model Calls --

    def log_model_call(
        self,
        call_id: str,
        model_name: str,
        provider: str,
        deployment_name: str = "",
        metrics: AiModelCallMetrics | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AiModelCall:
        call = AiModelCall(
            call_id=call_id,
            model_name=model_name,
            provider=provider,
            deployment_name=deployment_name,
            metrics=metrics or AiModelCallMetrics(),
            metadata=metadata or {},
        )
        self._model_calls[call_id] = call
        AiModelCallLogged(
            call_id=call_id,
            model_name=model_name,
            provider=provider,
            deployment_name=deployment_name,
            metrics=metrics,
            metadata=metadata,
        )
        self._log.info("model_call.logged", call_id=call_id, model=model_name)
        return call

    def get_model_call(self, call_id: str) -> AiModelCall | None:
        return self._model_calls.get(call_id)

    def list_model_calls(self) -> list[AiModelCall]:
        return list(self._model_calls.values())

    # -- Reporting --

    def generate_report(
        self,
        title: str,
        description: str = "",
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> AiObservabilityReport:
        now = utc_now()
        report = AiObservabilityReport(
            report_id=str(uuid4()),
            title=title,
            description=description,
            period_start=period_start or now,
            period_end=period_end or now,
            traces=tuple(span for spans in self._traces.values() for span in spans),
            model_calls=tuple(self._model_calls.values()),
            metrics=tuple(m for metrics in self._metrics.values() for m in metrics),
            alerts=tuple(self._alerts.values()),
        )
        self._reports[report.report_id] = report
        AiObservabilityReportGenerated(
            report_id=report.report_id,
            title=title,
            period_start=report.period_start,
            period_end=report.period_end,
            trace_count=len(report.traces),
            model_call_count=len(report.model_calls),
            alert_count=len(report.alerts),
        )
        self._log.info("report.generated", report_id=report.report_id)
        return report

    def get_report(self, report_id: str) -> AiObservabilityReport:
        report = self._reports.get(report_id)
        if report is None:
            raise AiObservabilityReportError(f"Report {report_id!r} not found")
        return report

    def list_reports(self) -> list[AiObservabilityReport]:
        return list(self._reports.values())

    # -- Alerting --

    def trigger_alert(
        self,
        rule_name: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        severity: AiObservabilityAlertSeverity = AiObservabilityAlertSeverity.WARNING,
        message: str = "",
    ) -> AiObservabilityAlert:
        alert = AiObservabilityAlert(
            alert_id=str(uuid4()),
            rule_name=rule_name,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            severity=severity,
            message=message
            or (f"{rule_name}: {metric_name}={current_value} (threshold={threshold})"),
        )
        self._alerts[alert.alert_id] = alert
        AiObservabilityAlertTriggered(
            alert_id=alert.alert_id,
            rule_name=rule_name,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            severity=severity,
            message=alert.message,
        )
        self._log.info("alert.triggered", alert_id=alert.alert_id, rule=rule_name)
        return alert

    def resolve_alert(self, alert_id: str) -> AiObservabilityAlert:
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise AiObservabilityAlertError(f"Alert {alert_id!r} not found")
        now = utc_now()
        updated = alert.model_copy(update={"status": "resolved", "resolved_at": now})
        self._alerts[alert_id] = updated
        AiObservabilityAlertResolved(
            alert_id=alert_id,
            rule_name=alert.rule_name,
            resolved_at=now,
        )
        self._log.info("alert.resolved", alert_id=alert_id)
        return updated

    def list_alerts(self, active_only: bool = False) -> list[AiObservabilityAlert]:
        alerts = list(self._alerts.values())
        if active_only:
            alerts = [a for a in alerts if a.status == "firing"]
        return alerts

    # -- Dashboards --

    def create_dashboard(
        self,
        name: str,
        description: str = "",
        widgets: tuple[dict[str, Any], ...] | None = None,
    ) -> AiObservabilityDashboard:
        dashboard = AiObservabilityDashboard(
            id=str(uuid4()),
            name=name,
            description=description,
            widgets=widgets or (),
        )
        self._dashboards[dashboard.id] = dashboard
        AiObservabilityDashboardCreated(
            dashboard_id=dashboard.id,
            dashboard_name=name,
        )
        self._log.info("dashboard.created", id=dashboard.id, name=name)
        return dashboard

    def update_dashboard(
        self,
        dashboard_id: str,
        **updates: Any,
    ) -> AiObservabilityDashboard:
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise AiObservabilityConfigError(f"Dashboard {dashboard_id!r} not found")
        updated = dashboard.model_copy(update=updates)
        self._dashboards[dashboard_id] = updated
        AiObservabilityDashboardUpdated(
            dashboard_id=dashboard_id,
            dashboard_name=updated.name,
        )
        self._log.info("dashboard.updated", id=dashboard_id)
        return updated

    def get_dashboard(self, dashboard_id: str) -> AiObservabilityDashboard:
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise AiObservabilityConfigError(f"Dashboard {dashboard_id!r} not found")
        return dashboard

    def list_dashboards(self) -> list[AiObservabilityDashboard]:
        return list(self._dashboards.values())

    def delete_dashboard(self, dashboard_id: str) -> None:
        if dashboard_id not in self._dashboards:
            raise AiObservabilityConfigError(f"Dashboard {dashboard_id!r} not found")
        del self._dashboards[dashboard_id]
        self._log.info("dashboard.deleted", id=dashboard_id)

    # -- Config --

    @property
    def config(self) -> AiObservabilityConfig:
        return self._config

    def update_config(self, **updates: Any) -> AiObservabilityConfig:
        old = self._config
        new = old.model_copy(update=updates)
        self._config = new
        AiObservabilityConfigUpdated(old_config=old, new_config=new)
        self._log.info("config.updated")
        return new


__all__ = ["AiObservabilityService"]
