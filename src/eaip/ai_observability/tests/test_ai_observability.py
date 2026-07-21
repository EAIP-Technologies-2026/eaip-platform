from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest

from eaip.ai_observability.events import (
    AiModelCallLogged,
    AiObservabilityAlertResolved,
    AiObservabilityAlertTriggered,
    AiObservabilityConfigUpdated,
    AiObservabilityDashboardCreated,
    AiObservabilityDashboardUpdated,
    AiObservabilityMetricRecorded,
    AiObservabilityReportGenerated,
    AiTraceContextPropagated,
    AiTraceSpanCompleted,
    AiTraceSpanFailed,
    AiTraceSpanStarted,
    AiTraceStarted,
)
from eaip.ai_observability.exceptions import (
    AiObservabilityAlertError,
    AiObservabilityConfigError,
    AiObservabilityError,
    AiObservabilityReportError,
    AiSpanError,
    AiTraceError,
)
from eaip.ai_observability.health import AiObservabilityHealthCheck
from eaip.ai_observability.integration import AiObservabilityRuntimeModule
from eaip.ai_observability.models import (
    AiModelCall,
    AiModelCallMetrics,
    AiObservabilityAlertSeverity,
    AiObservabilityConfig,
    AiObservabilityDashboard,
    AiObservabilityReport,
    AiTraceContext,
    AiTraceSpan,
    AiTraceSpanStatus,
    LatencyBreakdown,
    MetricType,
    SpanKind,
    TokenUsage,
)
from eaip.ai_observability.service import AiObservabilityService


class TestModels:
    def test_ai_trace_span_defaults(self) -> None:
        span = AiTraceSpan(span_id="s1", trace_id="t1", name="test")
        assert span.kind == SpanKind.INTERNAL
        assert span.status == AiTraceSpanStatus.OK
        assert span.end_time is None

    def test_token_usage_defaults(self) -> None:
        t = TokenUsage()
        assert t.prompt_tokens == 0
        assert t.completion_tokens == 0
        assert t.total_tokens == 0

    def test_latency_breakdown_defaults(self) -> None:
        lb = LatencyBreakdown()
        assert lb.ttft_ms == 0.0
        assert lb.total_ms == 0.0

    def test_ai_observability_config_defaults(self) -> None:
        cfg = AiObservabilityConfig()
        assert cfg.tracing_enabled is True
        assert cfg.sampling_rate == 1.0
        assert cfg.report_interval_seconds == 3600

    def test_ai_model_call_with_metrics(self) -> None:
        metrics = AiModelCallMetrics(
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            latency=LatencyBreakdown(total_ms=150.0),
        )
        call = AiModelCall(call_id="c1", model_name="gpt-4", provider="openai", metrics=metrics)
        assert call.metrics.token_usage.total_tokens == 30
        assert call.metrics.latency.total_ms == 150.0

    def test_ai_observability_alert_severity_values(self) -> None:
        assert AiObservabilityAlertSeverity.INFO.value == "info"
        assert AiObservabilityAlertSeverity.WARNING.value == "warning"
        assert AiObservabilityAlertSeverity.CRITICAL.value == "critical"
        assert AiObservabilityAlertSeverity.FATAL.value == "fatal"

    def test_metric_type_values(self) -> None:
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"

    def test_span_kind_values(self) -> None:
        assert SpanKind.INTERNAL.value == "internal"
        assert SpanKind.SERVER.value == "server"
        assert SpanKind.CLIENT.value == "client"

    def test_ai_observability_report_with_traces(self) -> None:
        span = AiTraceSpan(span_id="s1", trace_id="t1", name="span1")
        report = AiObservabilityReport(
            report_id="r1",
            title="Test",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 2),
            traces=(span,),
        )
        assert len(report.traces) == 1
        assert report.traces[0].name == "span1"

    def test_ai_trace_context_creation(self) -> None:
        ctx = AiTraceContext(trace_id="t1", span_id="s1", parent_span_id="ps1")
        assert ctx.trace_id == "t1"
        assert ctx.span_id == "s1"
        assert ctx.parent_span_id == "ps1"
        assert ctx.baggage == {}

    def test_ai_observability_dashboard_defaults(self) -> None:
        db = AiObservabilityDashboard(id="d1", name="Dashboard")
        assert db.enabled is True
        assert db.refresh_interval_seconds == 60
        assert db.widgets == ()


class TestEvents:
    def test_ai_trace_started_event_type(self) -> None:
        ev = AiTraceStarted(trace_id="t1", name="trace1")
        assert ev.event_type == "eaip.ai_observability.trace.started"

    def test_ai_trace_span_started_event_type(self) -> None:
        ev = AiTraceSpanStarted(span_id="s1", trace_id="t1", name="span1")
        assert ev.event_type == "eaip.ai_observability.trace.span.started"

    def test_ai_trace_span_completed_event_type(self) -> None:
        ev = AiTraceSpanCompleted(span_id="s1", trace_id="t1")
        assert ev.event_type == "eaip.ai_observability.trace.span.completed"

    def test_ai_trace_span_failed_event_type(self) -> None:
        ev = AiTraceSpanFailed(span_id="s1", trace_id="t1", error_message="err")
        assert ev.event_type == "eaip.ai_observability.trace.span.failed"

    def test_ai_model_call_logged_event_type(self) -> None:
        ev = AiModelCallLogged(call_id="c1", model_name="gpt4", provider="openai")
        assert ev.event_type == "eaip.ai_observability.model_call.logged"

    def test_ai_observability_metric_recorded_event_type(self) -> None:
        ev = AiObservabilityMetricRecorded(name="m1", type=MetricType.COUNTER, value=1.0)
        assert ev.event_type == "eaip.ai_observability.metric.recorded"

    def test_ai_observability_report_generated_event_type(self) -> None:
        ev = AiObservabilityReportGenerated(
            report_id="r1",
            title="Report",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 2),
        )
        assert ev.event_type == "eaip.ai_observability.report.generated"

    def test_ai_observability_alert_triggered_event_type(self) -> None:
        ev = AiObservabilityAlertTriggered(
            alert_id="a1",
            rule_name="high-latency",
            metric_name="latency",
            current_value=2000.0,
            threshold=1000.0,
        )
        assert ev.event_type == "eaip.ai_observability.alert.triggered"

    def test_ai_observability_alert_resolved_event_type(self) -> None:
        ev = AiObservabilityAlertResolved(alert_id="a1", rule_name="high-latency")
        assert ev.event_type == "eaip.ai_observability.alert.resolved"

    def test_ai_trace_context_propagated_event_type(self) -> None:
        ev = AiTraceContextPropagated(trace_id="t1", span_id="s1")
        assert ev.event_type == "eaip.ai_observability.trace.context.propagated"

    def test_ai_observability_config_updated_event_type(self) -> None:
        ev = AiObservabilityConfigUpdated(new_config=AiObservabilityConfig())
        assert ev.event_type == "eaip.ai_observability.config.updated"

    def test_ai_observability_dashboard_created_event_type(self) -> None:
        ev = AiObservabilityDashboardCreated(dashboard_id="d1", dashboard_name="DB")
        assert ev.event_type == "eaip.ai_observability.dashboard.created"

    def test_ai_observability_dashboard_updated_event_type(self) -> None:
        ev = AiObservabilityDashboardUpdated(dashboard_id="d1", dashboard_name="DB")
        assert ev.event_type == "eaip.ai_observability.dashboard.updated"


class TestExceptions:
    def test_ai_observability_error_is_eaip_error(self) -> None:
        err = AiObservabilityError("test")
        assert err.message == "test"

    def test_ai_trace_error_inheritance(self) -> None:
        err = AiTraceError("trace error")
        assert isinstance(err, AiObservabilityError)

    def test_ai_span_error_inheritance(self) -> None:
        err = AiSpanError("span error")
        assert isinstance(err, AiObservabilityError)

    def test_ai_observability_config_error(self) -> None:
        err = AiObservabilityConfigError("bad config")
        assert isinstance(err, AiObservabilityError)

    def test_ai_observability_report_error(self) -> None:
        err = AiObservabilityReportError("report failed")
        assert isinstance(err, AiObservabilityError)

    def test_ai_observability_alert_error(self) -> None:
        err = AiObservabilityAlertError("alert failed")
        assert isinstance(err, AiObservabilityError)


class TestServiceTrace:
    def test_start_trace_returns_uuid(self) -> None:
        svc = AiObservabilityService()
        tid = svc.start_trace("test-trace")
        UUID(tid)

    def test_start_span_adds_to_trace(self) -> None:
        svc = AiObservabilityService()
        tid = svc.start_trace("trace")
        svc.start_span(tid, "span1")
        assert len(svc.get_trace_spans(tid)) == 1

    def test_complete_span_updates_status(self) -> None:
        svc = AiObservabilityService()
        tid = svc.start_trace("trace")
        sid = svc.start_span(tid, "span1")
        completed = svc.complete_span(sid)
        assert completed.status == AiTraceSpanStatus.OK
        assert completed.end_time is not None

    def test_fail_span_sets_error(self) -> None:
        svc = AiObservabilityService()
        tid = svc.start_trace("trace")
        sid = svc.start_span(tid, "span1")
        failed = svc.fail_span(sid, "something went wrong", "ValueError")
        assert failed.status == AiTraceSpanStatus.ERROR
        assert failed.attributes.get("error.type") == "ValueError"

    def test_start_span_unknown_trace_raises(self) -> None:
        svc = AiObservabilityService()
        with pytest.raises(AiTraceError):
            svc.start_span("unknown", "span1")

    def test_complete_unknown_span_raises(self) -> None:
        svc = AiObservabilityService()
        with pytest.raises(AiTraceError):
            svc.complete_span("unknown")

    def test_current_context_returns_none_for_empty_trace(self) -> None:
        svc = AiObservabilityService()
        ctx = svc.current_context("nonexistent")
        assert ctx is None

    def test_current_context_returns_latest_span(self) -> None:
        svc = AiObservabilityService()
        tid = svc.start_trace("trace")
        svc.start_span(tid, "span1")
        ctx = svc.current_context(tid)
        assert ctx is not None
        assert ctx.trace_id == tid


class TestServiceMetrics:
    def test_record_metric_stores_value(self) -> None:
        svc = AiObservabilityService()
        m = svc.record_metric("test_metric", MetricType.COUNTER, 42.0, labels={"env": "test"})
        assert m.value == 42.0
        assert m.labels == {"env": "test"}

    def test_get_metrics_returns_recorded(self) -> None:
        svc = AiObservabilityService()
        svc.record_metric("cpu", MetricType.GAUGE, 0.5)
        metrics = svc.get_metrics("cpu")
        assert len(metrics) == 1
        assert metrics[0].value == 0.5


class TestServiceModelCalls:
    def test_log_model_call(self) -> None:
        svc = AiObservabilityService()
        call = svc.log_model_call("c1", "gpt-4", "openai")
        assert call.model_name == "gpt-4"

    def test_get_model_call_returns_none_for_missing(self) -> None:
        svc = AiObservabilityService()
        assert svc.get_model_call("nonexistent") is None

    def test_list_model_calls(self) -> None:
        svc = AiObservabilityService()
        svc.log_model_call("c1", "gpt-4", "openai")
        svc.log_model_call("c2", "claude-3", "anthropic")
        assert len(svc.list_model_calls()) == 2


class TestServiceReporting:
    def test_generate_report_creates_report(self) -> None:
        svc = AiObservabilityService()
        report = svc.generate_report("Test Report", "A test")
        assert report.title == "Test Report"
        assert UUID(report.report_id)

    def test_get_report_returns_report(self) -> None:
        svc = AiObservabilityService()
        report = svc.generate_report("Test")
        fetched = svc.get_report(report.report_id)
        assert fetched.report_id == report.report_id

    def test_get_report_raises_for_missing(self) -> None:
        svc = AiObservabilityService()
        with pytest.raises(AiObservabilityReportError):
            svc.get_report("nonexistent")


class TestServiceAlerting:
    def test_trigger_alert_creates_alert(self) -> None:
        svc = AiObservabilityService()
        alert = svc.trigger_alert("high-latency", "p99_latency", 2000.0, 1000.0)
        assert alert.rule_name == "high-latency"
        assert alert.status == "firing"

    def test_resolve_alert_updates_status(self) -> None:
        svc = AiObservabilityService()
        alert = svc.trigger_alert("high-latency", "p99_latency", 2000.0, 1000.0)
        resolved = svc.resolve_alert(alert.alert_id)
        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None

    def test_resolve_unknown_alert_raises(self) -> None:
        svc = AiObservabilityService()
        with pytest.raises(AiObservabilityAlertError):
            svc.resolve_alert("unknown")

    def test_list_alerts_active_only(self) -> None:
        svc = AiObservabilityService()
        svc.trigger_alert("a1", "m1", 1.0, 0.5)
        a2 = svc.trigger_alert("a2", "m2", 1.0, 0.5)
        svc.resolve_alert(a2.alert_id)
        assert len(svc.list_alerts(active_only=True)) == 1


class TestServiceDashboards:
    def test_create_dashboard(self) -> None:
        svc = AiObservabilityService()
        db = svc.create_dashboard("AI Dashboard", "Dashboard for AI metrics")
        assert db.name == "AI Dashboard"
        assert UUID(db.id)

    def test_get_dashboard_returns_created(self) -> None:
        svc = AiObservabilityService()
        db = svc.create_dashboard("DB")
        fetched = svc.get_dashboard(db.id)
        assert fetched.id == db.id

    def test_get_dashboard_raises_for_missing(self) -> None:
        svc = AiObservabilityService()
        with pytest.raises(AiObservabilityConfigError):
            svc.get_dashboard("nonexistent")

    def test_update_dashboard(self) -> None:
        svc = AiObservabilityService()
        db = svc.create_dashboard("DB")
        updated = svc.update_dashboard(db.id, name="Updated DB")
        assert updated.name == "Updated DB"

    def test_delete_dashboard(self) -> None:
        svc = AiObservabilityService()
        db = svc.create_dashboard("DB")
        svc.delete_dashboard(db.id)
        with pytest.raises(AiObservabilityConfigError):
            svc.get_dashboard(db.id)

    def test_list_dashboards(self) -> None:
        svc = AiObservabilityService()
        svc.create_dashboard("DB1")
        svc.create_dashboard("DB2")
        assert len(svc.list_dashboards()) == 2


class TestServiceConfig:
    def test_update_config(self) -> None:
        svc = AiObservabilityService()
        updated = svc.update_config(sampling_rate=0.5, tracing_enabled=False)
        assert updated.sampling_rate == 0.5
        assert updated.tracing_enabled is False

    def test_config_property(self) -> None:
        cfg = AiObservabilityConfig(max_traces=500)
        svc = AiObservabilityService(config=cfg)
        assert svc.config.max_traces == 500


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        hc = AiObservabilityHealthCheck(trace_count=5, model_call_count=10, alert_count=2)
        report = await hc.check()
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_degraded(self) -> None:
        hc = AiObservabilityHealthCheck()
        report = await hc.check()
        assert report.status.value == "degraded"
        assert "No traces recorded" in report.message

    @pytest.mark.asyncio
    async def test_health_check_component_name(self) -> None:
        hc = AiObservabilityHealthCheck()
        report = await hc.check()
        assert report.component == "ai_observability"

    @pytest.mark.asyncio
    async def test_health_check_details(self) -> None:
        hc = AiObservabilityHealthCheck(trace_count=3, model_call_count=7, alert_count=1)
        report = await hc.check()
        assert report.details["traces_total"] == 3
        assert report.details["model_calls_total"] == 7
        assert report.details["alerts_total"] == 1


class TestIntegration:
    def test_module_name(self) -> None:
        mod = AiObservabilityRuntimeModule()
        assert mod.name == "ai_observability"

    def test_module_has_service(self) -> None:
        mod = AiObservabilityRuntimeModule()
        assert mod.service is not None
        assert isinstance(mod.service, AiObservabilityService)

    def test_module_with_custom_service(self) -> None:
        svc = AiObservabilityService()
        mod = AiObservabilityRuntimeModule(service=svc)
        assert mod.service is svc
