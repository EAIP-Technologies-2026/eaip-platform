from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest

from eaip.runtime_diagnostics.events import (
    DiagnosticsAlertResolved,
    DiagnosticsAlertTriggered,
    DiagnosticsCheckCompleted,
    DiagnosticsCheckFailed,
    DiagnosticsCheckStarted,
    DiagnosticsCollectorStatusChanged,
    DiagnosticsDashboardUpdated,
    DiagnosticsHistoryEntryRecorded,
    DiagnosticsMetricCollected,
    DiagnosticsProbeCreated,
    DiagnosticsProbeExecuted,
    DiagnosticsProbeFailed,
    DiagnosticsReportGenerated,
    DiagnosticsSnapshotTaken,
    RuntimeDiagnosticsConfigUpdated,
)
from eaip.runtime_diagnostics.exceptions import (
    DiagnosticsAlertError,
    DiagnosticsCheckError,
    DiagnosticsCollectorError,
    DiagnosticsConfigError,
    DiagnosticsProbeError,
    DiagnosticsReportError,
    DiagnosticsSnapshotError,
    RuntimeDiagnosticsError,
)
from eaip.runtime_diagnostics.health import RuntimeDiagnosticsHealthCheck
from eaip.runtime_diagnostics.integration import RuntimeDiagnosticsRuntimeModule
from eaip.runtime_diagnostics.models import (
    DiagnosticsAlert,
    DiagnosticsCheck,
    DiagnosticsCollector,
    DiagnosticsCollectorStatus,
    DiagnosticsDashboard,
    DiagnosticsHistoryEntry,
    DiagnosticsMetric,
    DiagnosticsMetricType,
    DiagnosticsProbe,
    DiagnosticsReport,
    DiagnosticsReportSeverity,
    DiagnosticsResult,
    DiagnosticsSnapshot,
    DiagnosticsStatus,
    DiagnosticsThreshold,
    ProbeType,
    RuntimeDiagnosticsConfig,
)
from eaip.runtime_diagnostics.service import RuntimeDiagnosticsService


class TestModels:
    def test_runtime_diagnostics_config_defaults(self) -> None:
        cfg = RuntimeDiagnosticsConfig()
        assert cfg.enabled is True
        assert cfg.probe_interval_seconds == 60
        assert cfg.check_interval_seconds == 300
        assert cfg.snapshot_retention_days == 7
        assert cfg.metric_retention_days == 30
        assert cfg.max_alerts == 100
        assert cfg.max_history_entries == 1000

    def test_diagnostics_probe_defaults(self) -> None:
        probe = DiagnosticsProbe(
            id="p1", name="http-probe", probe_type=ProbeType.HTTP, target="http://localhost"
        )
        assert probe.enabled is True
        assert probe.interval_seconds == 60
        assert probe.timeout_seconds == 30
        assert probe.metadata == {}

    def test_diagnostics_result_defaults(self) -> None:
        result = DiagnosticsResult(probe_id="p1", status=DiagnosticsStatus.PASS)
        assert result.latency_ms == 0.0
        assert result.message == ""
        assert result.details == {}
        assert isinstance(result.checked_at, datetime)

    def test_diagnostics_check_defaults(self) -> None:
        check = DiagnosticsCheck(id="c1", name="system-check")
        assert check.enabled is True
        assert check.interval_seconds == 300
        assert check.description == ""
        assert check.probe_ids == ()

    def test_diagnostics_report_defaults(self) -> None:
        report = DiagnosticsReport(id="r1", title="Health Report")
        assert report.severity == DiagnosticsReportSeverity.INFO
        assert report.description == ""
        assert report.checks == ()

    def test_diagnostics_alert_defaults(self) -> None:
        alert = DiagnosticsAlert(id="a1", rule_name="high-cpu", message="CPU too high")
        assert alert.severity == DiagnosticsReportSeverity.WARNING
        assert alert.status == "firing"
        assert alert.resolved_at is None
        assert alert.details == {}

    def test_diagnostics_snapshot_defaults(self) -> None:
        snap = DiagnosticsSnapshot(id="s1", label="pre-upgrade")
        assert snap.snapshot_type == "full"
        assert snap.data == {}
        assert snap.size_bytes == 0

    def test_diagnostics_metric_defaults(self) -> None:
        m = DiagnosticsMetric(name="cpu", type=DiagnosticsMetricType.GAUGE, value=0.5)
        assert m.labels == {}
        assert m.unit == ""

    def test_diagnostics_dashboard_defaults(self) -> None:
        db = DiagnosticsDashboard(id="d1", name="Runtime Dashboard")
        assert db.enabled is True
        assert db.refresh_interval_seconds == 60
        assert db.widgets == ()

    def test_diagnostics_collector_defaults(self) -> None:
        c = DiagnosticsCollector(id="col1", name="default-collector")
        assert c.status == DiagnosticsCollectorStatus.STOPPED
        assert c.config == {}
        assert c.started_at is None

    def test_diagnostics_history_entry_defaults(self) -> None:
        entry = DiagnosticsHistoryEntry(id="h1", action="restart", component="probe-manager")
        assert entry.severity == DiagnosticsReportSeverity.INFO
        assert entry.message == ""
        assert entry.details == {}

    def test_diagnostics_threshold_creation(self) -> None:
        t = DiagnosticsThreshold(metric_name="cpu", warning_threshold=80.0, critical_threshold=95.0)
        assert t.operator == "gt"
        assert t.enabled is True

    def test_probe_type_values(self) -> None:
        assert ProbeType.HTTP.value == "http"
        assert ProbeType.TCP.value == "tcp"
        assert ProbeType.PROCESS.value == "process"
        assert ProbeType.CUSTOM.value == "custom"

    def test_diagnostics_status_values(self) -> None:
        assert DiagnosticsStatus.PASS.value == "pass"
        assert DiagnosticsStatus.FAIL.value == "fail"
        assert DiagnosticsStatus.WARN.value == "warn"
        assert DiagnosticsStatus.SKIP.value == "skip"

    def test_diagnostics_report_severity_values(self) -> None:
        assert DiagnosticsReportSeverity.INFO.value == "info"
        assert DiagnosticsReportSeverity.WARNING.value == "warning"
        assert DiagnosticsReportSeverity.ERROR.value == "error"
        assert DiagnosticsReportSeverity.CRITICAL.value == "critical"

    def test_diagnostics_metric_type_values(self) -> None:
        assert DiagnosticsMetricType.COUNTER.value == "counter"
        assert DiagnosticsMetricType.GAUGE.value == "gauge"
        assert DiagnosticsMetricType.HISTOGRAM.value == "histogram"

    def test_diagnostics_collector_status_values(self) -> None:
        assert DiagnosticsCollectorStatus.RUNNING.value == "running"
        assert DiagnosticsCollectorStatus.STOPPED.value == "stopped"
        assert DiagnosticsCollectorStatus.PAUSED.value == "paused"
        assert DiagnosticsCollectorStatus.ERROR.value == "error"

    def test_runtime_diagnostics_config_immutable(self) -> None:
        cfg = RuntimeDiagnosticsConfig()
        with pytest.raises(ValueError, match="frozen"):
            cfg.enabled = False


class TestEvents:
    def test_config_updated_event_type(self) -> None:
        ev = RuntimeDiagnosticsConfigUpdated(new_config=RuntimeDiagnosticsConfig())
        assert ev.event_type == "eaip.runtime_diagnostics.config.updated"

    def test_probe_created_event_type(self) -> None:
        ev = DiagnosticsProbeCreated(
            probe_id="p1",
            name="probe1",
            probe_type="http",
            target="localhost",
        )
        assert ev.event_type == "eaip.runtime_diagnostics.probe.created"

    def test_probe_executed_event_type(self) -> None:
        ev = DiagnosticsProbeExecuted(probe_id="p1", status="pass", latency_ms=1.5)
        assert ev.event_type == "eaip.runtime_diagnostics.probe.executed"

    def test_probe_failed_event_type(self) -> None:
        ev = DiagnosticsProbeFailed(probe_id="p1", error_message="timeout")
        assert ev.event_type == "eaip.runtime_diagnostics.probe.failed"

    def test_check_started_event_type(self) -> None:
        ev = DiagnosticsCheckStarted(check_id="c1", name="check1")
        assert ev.event_type == "eaip.runtime_diagnostics.check.started"

    def test_check_completed_event_type(self) -> None:
        ev = DiagnosticsCheckCompleted(check_id="c1", name="check1", status="pass")
        assert ev.event_type == "eaip.runtime_diagnostics.check.completed"

    def test_check_failed_event_type(self) -> None:
        ev = DiagnosticsCheckFailed(check_id="c1", name="check1", error_message="err")
        assert ev.event_type == "eaip.runtime_diagnostics.check.failed"

    def test_report_generated_event_type(self) -> None:
        ev = DiagnosticsReportGenerated(
            report_id="r1",
            title="Report",
            severity=DiagnosticsReportSeverity.INFO,
        )
        assert ev.event_type == "eaip.runtime_diagnostics.report.generated"

    def test_alert_triggered_event_type(self) -> None:
        ev = DiagnosticsAlertTriggered(
            alert_id="a1",
            rule_name="high-cpu",
            message="CPU high",
            severity=DiagnosticsReportSeverity.WARNING,
        )
        assert ev.event_type == "eaip.runtime_diagnostics.alert.triggered"

    def test_alert_resolved_event_type(self) -> None:
        ev = DiagnosticsAlertResolved(
            alert_id="a1",
            rule_name="high-cpu",
            resolved_at=datetime(2024, 1, 1),
        )
        assert ev.event_type == "eaip.runtime_diagnostics.alert.resolved"

    def test_snapshot_taken_event_type(self) -> None:
        ev = DiagnosticsSnapshotTaken(snapshot_id="s1", label="snap1", snapshot_type="full")
        assert ev.event_type == "eaip.runtime_diagnostics.snapshot.taken"

    def test_metric_collected_event_type(self) -> None:
        ev = DiagnosticsMetricCollected(name="cpu", type=DiagnosticsMetricType.GAUGE, value=0.5)
        assert ev.event_type == "eaip.runtime_diagnostics.metric.collected"

    def test_history_entry_recorded_event_type(self) -> None:
        ev = DiagnosticsHistoryEntryRecorded(
            entry_id="h1",
            action="restart",
            component="probe-manager",
            severity=DiagnosticsReportSeverity.INFO,
        )
        assert ev.event_type == "eaip.runtime_diagnostics.history.recorded"

    def test_dashboard_updated_event_type(self) -> None:
        ev = DiagnosticsDashboardUpdated(dashboard_id="d1", dashboard_name="DB")
        assert ev.event_type == "eaip.runtime_diagnostics.dashboard.updated"

    def test_collector_status_changed_event_type(self) -> None:
        ev = DiagnosticsCollectorStatusChanged(
            collector_id="col1",
            name="collector1",
            new_status=DiagnosticsCollectorStatus.RUNNING,
        )
        assert ev.event_type == "eaip.runtime_diagnostics.collector.status_changed"


class TestExceptions:
    def test_runtime_diagnostics_error_is_eaip_error(self) -> None:
        err = RuntimeDiagnosticsError("test")
        assert err.message == "test"

    def test_diagnostics_config_error_inheritance(self) -> None:
        err = DiagnosticsConfigError("bad config")
        assert isinstance(err, RuntimeDiagnosticsError)

    def test_diagnostics_probe_error_inheritance(self) -> None:
        err = DiagnosticsProbeError("probe error")
        assert isinstance(err, RuntimeDiagnosticsError)

    def test_diagnostics_check_error_inheritance(self) -> None:
        err = DiagnosticsCheckError("check error")
        assert isinstance(err, RuntimeDiagnosticsError)

    def test_diagnostics_report_error_inheritance(self) -> None:
        err = DiagnosticsReportError("report error")
        assert isinstance(err, RuntimeDiagnosticsError)

    def test_diagnostics_alert_error_inheritance(self) -> None:
        err = DiagnosticsAlertError("alert error")
        assert isinstance(err, RuntimeDiagnosticsError)

    def test_diagnostics_collector_error_inheritance(self) -> None:
        err = DiagnosticsCollectorError("collector error")
        assert isinstance(err, RuntimeDiagnosticsError)

    def test_diagnostics_snapshot_error_inheritance(self) -> None:
        err = DiagnosticsSnapshotError("snapshot error")
        assert isinstance(err, RuntimeDiagnosticsError)


class TestServiceProbes:
    def test_create_probe_returns_probe(self) -> None:
        svc = RuntimeDiagnosticsService()
        probe = svc.create_probe("http-check", ProbeType.HTTP, "http://localhost")
        assert probe.name == "http-check"
        assert probe.probe_type == ProbeType.HTTP
        UUID(probe.id)

    def test_get_probe_returns_created(self) -> None:
        svc = RuntimeDiagnosticsService()
        probe = svc.create_probe("p1", ProbeType.HTTP, "http://localhost")
        fetched = svc.get_probe(probe.id)
        assert fetched.id == probe.id

    def test_get_probe_raises_for_missing(self) -> None:
        svc = RuntimeDiagnosticsService()
        with pytest.raises(DiagnosticsProbeError):
            svc.get_probe("nonexistent")

    def test_list_probes(self) -> None:
        svc = RuntimeDiagnosticsService()
        svc.create_probe("p1", ProbeType.HTTP, "http://a")
        svc.create_probe("p2", ProbeType.TCP, "localhost:8080")
        assert len(svc.list_probes()) == 2

    def test_delete_probe_removes_probe(self) -> None:
        svc = RuntimeDiagnosticsService()
        probe = svc.create_probe("p1", ProbeType.HTTP, "http://a")
        svc.delete_probe(probe.id)
        assert len(svc.list_probes()) == 0

    def test_delete_probe_raises_for_missing(self) -> None:
        svc = RuntimeDiagnosticsService()
        with pytest.raises(DiagnosticsProbeError):
            svc.delete_probe("nonexistent")

    def test_execute_probe_returns_result(self) -> None:
        svc = RuntimeDiagnosticsService()
        probe = svc.create_probe("p1", ProbeType.CUSTOM, "custom://check")
        result = svc.execute_probe(probe.id)
        assert isinstance(result, DiagnosticsResult)
        assert result.probe_id == probe.id

    def test_execute_probe_raises_for_missing(self) -> None:
        svc = RuntimeDiagnosticsService()
        with pytest.raises(DiagnosticsProbeError):
            svc.execute_probe("nonexistent")


class TestServiceChecks:
    def test_create_check(self) -> None:
        svc = RuntimeDiagnosticsService()
        check = svc.create_check("system-check")
        assert check.name == "system-check"
        UUID(check.id)

    def test_get_check_returns_created(self) -> None:
        svc = RuntimeDiagnosticsService()
        check = svc.create_check("c1")
        fetched = svc.get_check(check.id)
        assert fetched.id == check.id

    def test_get_check_raises_for_missing(self) -> None:
        svc = RuntimeDiagnosticsService()
        with pytest.raises(DiagnosticsCheckError):
            svc.get_check("nonexistent")

    def test_run_check_with_probes(self) -> None:
        svc = RuntimeDiagnosticsService()
        probe = svc.create_probe("p1", ProbeType.CUSTOM, "custom://check")
        check = svc.create_check("c1", probe_ids=(probe.id,))
        result = svc.run_check(check.id)
        assert len(result.results) > 0

    def test_delete_check(self) -> None:
        svc = RuntimeDiagnosticsService()
        check = svc.create_check("c1")
        svc.delete_check(check.id)
        assert len(svc.list_checks()) == 0


class TestServiceReports:
    def test_generate_report(self) -> None:
        svc = RuntimeDiagnosticsService()
        report = svc.generate_report("Health Report")
        assert report.title == "Health Report"
        UUID(report.id)

    def test_get_report_returns_report(self) -> None:
        svc = RuntimeDiagnosticsService()
        report = svc.generate_report("Test")
        fetched = svc.get_report(report.id)
        assert fetched.id == report.id

    def test_get_report_raises_for_missing(self) -> None:
        svc = RuntimeDiagnosticsService()
        with pytest.raises(DiagnosticsReportError):
            svc.get_report("nonexistent")

    def test_list_reports(self) -> None:
        svc = RuntimeDiagnosticsService()
        svc.generate_report("R1")
        svc.generate_report("R2")
        assert len(svc.list_reports()) == 2


class TestServiceAlerts:
    def test_trigger_alert(self) -> None:
        svc = RuntimeDiagnosticsService()
        alert = svc.trigger_alert("high-cpu", "CPU too high")
        assert alert.rule_name == "high-cpu"
        assert alert.status == "firing"

    def test_resolve_alert(self) -> None:
        svc = RuntimeDiagnosticsService()
        alert = svc.trigger_alert("high-cpu", "CPU too high")
        resolved = svc.resolve_alert(alert.id)
        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None

    def test_resolve_unknown_alert_raises(self) -> None:
        svc = RuntimeDiagnosticsService()
        with pytest.raises(DiagnosticsAlertError):
            svc.resolve_alert("unknown")

    def test_list_alerts_active_only(self) -> None:
        svc = RuntimeDiagnosticsService()
        a1 = svc.trigger_alert("a1", "msg1")
        a2 = svc.trigger_alert("a2", "msg2")
        svc.resolve_alert(a2.id)
        alerts = svc.list_alerts(active_only=True)
        assert len(alerts) == 1
        assert alerts[0].id == a1.id


class TestServiceSnapshots:
    def test_take_snapshot(self) -> None:
        svc = RuntimeDiagnosticsService()
        snap = svc.take_snapshot("pre-upgrade")
        assert snap.label == "pre-upgrade"
        UUID(snap.id)

    def test_get_snapshot_returns_snapshot(self) -> None:
        svc = RuntimeDiagnosticsService()
        snap = svc.take_snapshot("snap1")
        fetched = svc.get_snapshot(snap.id)
        assert fetched.id == snap.id

    def test_get_snapshot_raises_for_missing(self) -> None:
        svc = RuntimeDiagnosticsService()
        with pytest.raises(DiagnosticsSnapshotError):
            svc.get_snapshot("nonexistent")


class TestServiceMetrics:
    def test_collect_metric(self) -> None:
        svc = RuntimeDiagnosticsService()
        m = svc.collect_metric("cpu", DiagnosticsMetricType.GAUGE, 0.5, labels={"host": "h1"})
        assert m.value == 0.5
        assert m.labels == {"host": "h1"}

    def test_get_metrics(self) -> None:
        svc = RuntimeDiagnosticsService()
        svc.collect_metric("cpu", DiagnosticsMetricType.GAUGE, 0.5)
        metrics = svc.get_metrics("cpu")
        assert len(metrics) == 1
        assert metrics[0].value == 0.5


class TestServiceDashboards:
    def test_create_dashboard(self) -> None:
        svc = RuntimeDiagnosticsService()
        db = svc.create_dashboard("Runtime Dashboard")
        assert db.name == "Runtime Dashboard"
        UUID(db.id)

    def test_get_dashboard_returns_created(self) -> None:
        svc = RuntimeDiagnosticsService()
        db = svc.create_dashboard("DB")
        fetched = svc.get_dashboard(db.id)
        assert fetched.id == db.id

    def test_get_dashboard_raises_for_missing(self) -> None:
        svc = RuntimeDiagnosticsService()
        with pytest.raises(DiagnosticsConfigError):
            svc.get_dashboard("nonexistent")

    def test_update_dashboard(self) -> None:
        svc = RuntimeDiagnosticsService()
        db = svc.create_dashboard("DB")
        updated = svc.update_dashboard(db.id, name="Updated DB")
        assert updated.name == "Updated DB"

    def test_delete_dashboard(self) -> None:
        svc = RuntimeDiagnosticsService()
        db = svc.create_dashboard("DB")
        svc.delete_dashboard(db.id)
        with pytest.raises(DiagnosticsConfigError):
            svc.get_dashboard(db.id)

    def test_list_dashboards(self) -> None:
        svc = RuntimeDiagnosticsService()
        svc.create_dashboard("DB1")
        svc.create_dashboard("DB2")
        assert len(svc.list_dashboards()) == 2


class TestServiceCollectors:
    def test_register_collector(self) -> None:
        svc = RuntimeDiagnosticsService()
        col = svc.register_collector("metrics-collector")
        assert col.name == "metrics-collector"
        assert col.status == DiagnosticsCollectorStatus.STOPPED
        UUID(col.id)

    def test_start_collector(self) -> None:
        svc = RuntimeDiagnosticsService()
        col = svc.register_collector("col1")
        started = svc.start_collector(col.id)
        assert started.status == DiagnosticsCollectorStatus.RUNNING
        assert started.started_at is not None

    def test_stop_collector(self) -> None:
        svc = RuntimeDiagnosticsService()
        col = svc.register_collector("col1")
        svc.start_collector(col.id)
        stopped = svc.stop_collector(col.id)
        assert stopped.status == DiagnosticsCollectorStatus.STOPPED
        assert stopped.stopped_at is not None


class TestServiceHistory:
    def test_record_history(self) -> None:
        svc = RuntimeDiagnosticsService()
        entry = svc.record_history("restart", "probe-manager", "Restarted probe manager")
        assert entry.action == "restart"
        assert entry.component == "probe-manager"
        UUID(entry.id)

    def test_get_history(self) -> None:
        svc = RuntimeDiagnosticsService()
        svc.record_history("start", "collector", "Started")
        svc.record_history("stop", "collector", "Stopped")
        assert len(svc.get_history()) == 2


class TestServiceThresholds:
    def test_set_threshold(self) -> None:
        svc = RuntimeDiagnosticsService()
        t = svc.set_threshold("cpu", 80.0, 95.0)
        assert t.metric_name == "cpu"
        assert t.warning_threshold == 80.0
        assert t.critical_threshold == 95.0

    def test_get_threshold(self) -> None:
        svc = RuntimeDiagnosticsService()
        svc.set_threshold("cpu", 80.0, 95.0)
        t = svc.get_threshold("cpu")
        assert t is not None
        assert t.warning_threshold == 80.0

    def test_get_threshold_returns_none_for_missing(self) -> None:
        svc = RuntimeDiagnosticsService()
        assert svc.get_threshold("nonexistent") is None

    def test_list_thresholds(self) -> None:
        svc = RuntimeDiagnosticsService()
        svc.set_threshold("cpu", 80.0, 95.0)
        svc.set_threshold("memory", 70.0, 90.0)
        assert len(svc.list_thresholds()) == 2


class TestServiceConfig:
    def test_update_config(self) -> None:
        svc = RuntimeDiagnosticsService()
        updated = svc.update_config(probe_interval_seconds=30, enabled=False)
        assert updated.probe_interval_seconds == 30
        assert updated.enabled is False

    def test_config_property(self) -> None:
        cfg = RuntimeDiagnosticsConfig(probe_interval_seconds=120)
        svc = RuntimeDiagnosticsService(config=cfg)
        assert svc.config.probe_interval_seconds == 120


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        hc = RuntimeDiagnosticsHealthCheck()
        report = await hc.check()
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_component_name(self) -> None:
        hc = RuntimeDiagnosticsHealthCheck()
        report = await hc.check()
        assert report.component == "runtime_diagnostics"

    @pytest.mark.asyncio
    async def test_health_check_message(self) -> None:
        hc = RuntimeDiagnosticsHealthCheck()
        report = await hc.check()
        assert "healthy" in report.message


class TestIntegration:
    def test_module_name(self) -> None:
        mod = RuntimeDiagnosticsRuntimeModule()
        assert mod.name == "runtime_diagnostics"

    def test_module_has_service(self) -> None:
        mod = RuntimeDiagnosticsRuntimeModule()
        assert mod.service is not None
        assert isinstance(mod.service, RuntimeDiagnosticsService)

    def test_module_with_custom_service(self) -> None:
        svc = RuntimeDiagnosticsService()
        mod = RuntimeDiagnosticsRuntimeModule(service=svc)
        assert mod.service is svc
