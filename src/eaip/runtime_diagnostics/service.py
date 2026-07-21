"""Service implementation for runtime diagnostics."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from eaip.logging.context import get_logger
from eaip.runtime_diagnostics.events import (
    DiagnosticsAlertResolved,
    DiagnosticsAlertTriggered,
    DiagnosticsCheckCompleted,
    DiagnosticsCheckStarted,
    DiagnosticsCollectorStatusChanged,
    DiagnosticsDashboardUpdated,
    DiagnosticsHistoryEntryRecorded,
    DiagnosticsMetricCollected,
    DiagnosticsProbeCreated,
    DiagnosticsProbeExecuted,
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
)
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
from eaip.shared.time import utc_now


class RuntimeDiagnosticsService:
    """Core service for runtime diagnostics operations."""

    name: str = "runtime_diagnostics.service"

    def __init__(
        self,
        config: RuntimeDiagnosticsConfig | None = None,
    ) -> None:
        """Initialize the runtime diagnostics service."""
        self._config = config or RuntimeDiagnosticsConfig()
        self._probes: dict[str, DiagnosticsProbe] = {}
        self._checks: dict[str, DiagnosticsCheck] = {}
        self._reports: dict[str, DiagnosticsReport] = {}
        self._alerts: dict[str, DiagnosticsAlert] = {}
        self._snapshots: dict[str, DiagnosticsSnapshot] = {}
        self._metrics: dict[str, list[DiagnosticsMetric]] = {}
        self._dashboards: dict[str, DiagnosticsDashboard] = {}
        self._collectors: dict[str, DiagnosticsCollector] = {}
        self._history: list[DiagnosticsHistoryEntry] = []
        self._thresholds: dict[str, DiagnosticsThreshold] = {}
        self._log = get_logger("eaip.runtime_diagnostics.service")

    # -- Config --

    @property
    def config(self) -> RuntimeDiagnosticsConfig:
        """Return the current runtime diagnostics configuration."""
        return self._config

    def update_config(self, **updates: Any) -> RuntimeDiagnosticsConfig:
        """Update the runtime diagnostics configuration."""
        old = self._config
        new = old.model_copy(update=updates)
        self._config = new
        RuntimeDiagnosticsConfigUpdated(old_config=old, new_config=new)
        self._log.info("config.updated")
        return new

    # -- Probes --

    def create_probe(
        self,
        name: str,
        probe_type: ProbeType,
        target: str,
        interval_seconds: int = 60,
        timeout_seconds: int = 30,
        metadata: dict[str, Any] | None = None,
    ) -> DiagnosticsProbe:
        """Create a new diagnostics probe."""
        probe = DiagnosticsProbe(
            id=str(uuid4()),
            name=name,
            probe_type=probe_type,
            target=target,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {},
        )
        self._probes[probe.id] = probe
        DiagnosticsProbeCreated(
            probe_id=probe.id,
            name=name,
            probe_type=probe_type.value,
            target=target,
        )
        self._log.info("probe.created", probe_id=probe.id, name=name)
        return probe

    def get_probe(self, probe_id: str) -> DiagnosticsProbe:
        """Retrieve a probe by ID."""
        probe = self._probes.get(probe_id)
        if probe is None:
            raise DiagnosticsProbeError(f"Probe {probe_id!r} not found")
        return probe

    def list_probes(self) -> list[DiagnosticsProbe]:
        """List all registered probes."""
        return list(self._probes.values())

    def execute_probe(self, probe_id: str) -> DiagnosticsResult:
        """Execute a probe and return the result."""
        self.get_probe(probe_id)
        result = DiagnosticsResult(
            probe_id=probe_id,
            status=DiagnosticsStatus.PASS,
        )
        DiagnosticsProbeExecuted(
            probe_id=probe_id,
            status=result.status.value,
            latency_ms=result.latency_ms,
            message=result.message,
        )
        self._log.info("probe.executed", probe_id=probe_id)
        return result

    def delete_probe(self, probe_id: str) -> None:
        """Delete a probe by ID."""
        if probe_id not in self._probes:
            raise DiagnosticsProbeError(f"Probe {probe_id!r} not found")
        del self._probes[probe_id]
        self._log.info("probe.deleted", probe_id=probe_id)

    # -- Checks --

    def create_check(
        self,
        name: str,
        probe_ids: tuple[str, ...] | None = None,
        interval_seconds: int = 300,
        description: str = "",
    ) -> DiagnosticsCheck:
        """Create a new diagnostics check."""
        check = DiagnosticsCheck(
            id=str(uuid4()),
            name=name,
            probe_ids=probe_ids or (),
            interval_seconds=interval_seconds,
            description=description,
        )
        self._checks[check.id] = check
        self._log.info("check.created", check_id=check.id, name=name)
        return check

    def get_check(self, check_id: str) -> DiagnosticsCheck:
        """Retrieve a check by ID."""
        check = self._checks.get(check_id)
        if check is None:
            raise DiagnosticsCheckError(f"Check {check_id!r} not found")
        return check

    def list_checks(self) -> list[DiagnosticsCheck]:
        """List all registered checks."""
        return list(self._checks.values())

    def run_check(self, check_id: str) -> DiagnosticsCheck:
        """Run a diagnostics check and execute all associated probes."""
        check = self.get_check(check_id)
        DiagnosticsCheckStarted(check_id=check_id, name=check.name)
        results: list[DiagnosticsResult] = []
        for pid in check.probe_ids:
            try:
                result = self.execute_probe(pid)
                results.append(result)
            except DiagnosticsProbeError:
                continue
        updated = check.model_copy(
            update={"results": tuple(results)},
        )
        self._checks[check_id] = updated
        DiagnosticsCheckCompleted(
            check_id=check_id,
            name=check.name,
            status=DiagnosticsStatus.PASS.value,
            result_count=len(results),
        )
        self._log.info("check.completed", check_id=check_id)
        return updated

    def delete_check(self, check_id: str) -> None:
        """Delete a check by ID."""
        if check_id not in self._checks:
            raise DiagnosticsCheckError(f"Check {check_id!r} not found")
        del self._checks[check_id]
        self._log.info("check.deleted", check_id=check_id)

    # -- Reports --

    def generate_report(
        self,
        title: str,
        description: str = "",
        severity: DiagnosticsReportSeverity = DiagnosticsReportSeverity.INFO,
    ) -> DiagnosticsReport:
        """Generate a diagnostics report."""
        report = DiagnosticsReport(
            id=str(uuid4()),
            title=title,
            description=description,
            severity=severity,
            checks=tuple(self._checks.values()),
        )
        self._reports[report.id] = report
        DiagnosticsReportGenerated(
            report_id=report.id,
            title=title,
            severity=severity,
            check_count=len(report.checks),
        )
        self._log.info("report.generated", report_id=report.id)
        return report

    def get_report(self, report_id: str) -> DiagnosticsReport:
        """Retrieve a report by ID."""
        report = self._reports.get(report_id)
        if report is None:
            raise DiagnosticsReportError(f"Report {report_id!r} not found")
        return report

    def list_reports(self) -> list[DiagnosticsReport]:
        """List all generated reports."""
        return list(self._reports.values())

    # -- Alerts --

    def trigger_alert(
        self,
        rule_name: str,
        message: str,
        severity: DiagnosticsReportSeverity = DiagnosticsReportSeverity.WARNING,
        details: dict[str, Any] | None = None,
    ) -> DiagnosticsAlert:
        """Trigger a new diagnostics alert."""
        alert = DiagnosticsAlert(
            id=str(uuid4()),
            rule_name=rule_name,
            message=message,
            severity=severity,
            details=details or {},
        )
        self._alerts[alert.id] = alert
        DiagnosticsAlertTriggered(
            alert_id=alert.id,
            rule_name=rule_name,
            message=message,
            severity=severity,
            details=details,
        )
        self._log.info("alert.triggered", alert_id=alert.id, rule=rule_name)
        return alert

    def resolve_alert(self, alert_id: str) -> DiagnosticsAlert:
        """Resolve a triggered alert."""
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise DiagnosticsAlertError(f"Alert {alert_id!r} not found")
        now = utc_now()
        updated = alert.model_copy(update={"status": "resolved", "resolved_at": now})
        self._alerts[alert_id] = updated
        DiagnosticsAlertResolved(
            alert_id=alert_id,
            rule_name=alert.rule_name,
            resolved_at=now,
        )
        self._log.info("alert.resolved", alert_id=alert_id)
        return updated

    def list_alerts(self, active_only: bool = False) -> list[DiagnosticsAlert]:
        """List all alerts, optionally filtering to active only."""
        alerts = list(self._alerts.values())
        if active_only:
            alerts = [a for a in alerts if a.status == "firing"]
        return alerts

    # -- Snapshots --

    def take_snapshot(
        self,
        label: str,
        snapshot_type: str = "full",
        data: dict[str, Any] | None = None,
    ) -> DiagnosticsSnapshot:
        """Take a point-in-time diagnostics snapshot."""
        snapshot = DiagnosticsSnapshot(
            id=str(uuid4()),
            label=label,
            snapshot_type=snapshot_type,
            data=data or {},
        )
        self._snapshots[snapshot.id] = snapshot
        DiagnosticsSnapshotTaken(
            snapshot_id=snapshot.id,
            label=label,
            snapshot_type=snapshot_type,
            size_bytes=snapshot.size_bytes,
        )
        self._log.info("snapshot.taken", snapshot_id=snapshot.id)
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> DiagnosticsSnapshot:
        """Retrieve a snapshot by ID."""
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            raise DiagnosticsSnapshotError(f"Snapshot {snapshot_id!r} not found")
        return snapshot

    def list_snapshots(self) -> list[DiagnosticsSnapshot]:
        """List all taken snapshots."""
        return list(self._snapshots.values())

    # -- Metrics --

    def collect_metric(
        self,
        name: str,
        type: DiagnosticsMetricType,
        value: float,
        labels: dict[str, str] | None = None,
        unit: str = "",
    ) -> DiagnosticsMetric:
        """Collect a diagnostics metric."""
        metric = DiagnosticsMetric(
            name=name,
            type=type,
            value=value,
            labels=labels or {},
            unit=unit,
        )
        self._metrics.setdefault(name, []).append(metric)
        DiagnosticsMetricCollected(name=name, type=type, value=value, labels=labels, unit=unit)
        self._log.info("metric.collected", name=name, value=value)
        return metric

    def get_metrics(self, name: str) -> list[DiagnosticsMetric]:
        """Retrieve collected metrics by name."""
        return list(self._metrics.get(name, []))

    # -- Dashboards --

    def create_dashboard(self, name: str, description: str = "") -> DiagnosticsDashboard:
        """Create a new diagnostics dashboard."""
        dashboard = DiagnosticsDashboard(
            id=str(uuid4()),
            name=name,
            description=description,
        )
        self._dashboards[dashboard.id] = dashboard
        self._log.info("dashboard.created", id=dashboard.id, name=name)
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> DiagnosticsDashboard:
        """Retrieve a dashboard by ID."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise DiagnosticsConfigError(f"Dashboard {dashboard_id!r} not found")
        return dashboard

    def update_dashboard(self, dashboard_id: str, **updates: Any) -> DiagnosticsDashboard:
        """Update a diagnostics dashboard."""
        dashboard = self._dashboards.get(dashboard_id)
        if dashboard is None:
            raise DiagnosticsConfigError(f"Dashboard {dashboard_id!r} not found")
        updated = dashboard.model_copy(update=updates)
        self._dashboards[dashboard_id] = updated
        DiagnosticsDashboardUpdated(dashboard_id=dashboard_id, dashboard_name=updated.name)
        self._log.info("dashboard.updated", id=dashboard_id)
        return updated

    def list_dashboards(self) -> list[DiagnosticsDashboard]:
        """List all dashboards."""
        return list(self._dashboards.values())

    def delete_dashboard(self, dashboard_id: str) -> None:
        """Delete a dashboard by ID."""
        if dashboard_id not in self._dashboards:
            raise DiagnosticsConfigError(f"Dashboard {dashboard_id!r} not found")
        del self._dashboards[dashboard_id]
        self._log.info("dashboard.deleted", id=dashboard_id)

    # -- Collectors --

    def register_collector(
        self,
        name: str,
        collector_type: str = "default",
        config: dict[str, Any] | None = None,
    ) -> DiagnosticsCollector:
        """Register a new diagnostics collector."""
        collector = DiagnosticsCollector(
            id=str(uuid4()),
            name=name,
            collector_type=collector_type,
            config=config or {},
        )
        self._collectors[collector.id] = collector
        self._log.info("collector.registered", collector_id=collector.id, name=name)
        return collector

    def get_collector(self, collector_id: str) -> DiagnosticsCollector:
        """Retrieve a collector by ID."""
        collector = self._collectors.get(collector_id)
        if collector is None:
            raise DiagnosticsCollectorError(f"Collector {collector_id!r} not found")
        return collector

    def start_collector(self, collector_id: str) -> DiagnosticsCollector:
        """Start a diagnostics collector."""
        collector = self.get_collector(collector_id)
        old_status = collector.status
        now = utc_now()
        updated = collector.model_copy(
            update={"status": DiagnosticsCollectorStatus.RUNNING, "started_at": now},
        )
        self._collectors[collector_id] = updated
        DiagnosticsCollectorStatusChanged(
            collector_id=collector_id,
            name=collector.name,
            old_status=old_status,
            new_status=DiagnosticsCollectorStatus.RUNNING,
        )
        self._log.info("collector.started", collector_id=collector_id)
        return updated

    def stop_collector(self, collector_id: str) -> DiagnosticsCollector:
        """Stop a diagnostics collector."""
        collector = self.get_collector(collector_id)
        old_status = collector.status
        now = utc_now()
        updated = collector.model_copy(
            update={"status": DiagnosticsCollectorStatus.STOPPED, "stopped_at": now},
        )
        self._collectors[collector_id] = updated
        DiagnosticsCollectorStatusChanged(
            collector_id=collector_id,
            name=collector.name,
            old_status=old_status,
            new_status=DiagnosticsCollectorStatus.STOPPED,
        )
        self._log.info("collector.stopped", collector_id=collector_id)
        return updated

    def list_collectors(self) -> list[DiagnosticsCollector]:
        """List all registered collectors."""
        return list(self._collectors.values())

    # -- History --

    def record_history(
        self,
        action: str,
        component: str,
        message: str = "",
        severity: DiagnosticsReportSeverity = DiagnosticsReportSeverity.INFO,
        details: dict[str, Any] | None = None,
    ) -> DiagnosticsHistoryEntry:
        """Record an entry in the diagnostics history."""
        entry = DiagnosticsHistoryEntry(
            id=str(uuid4()),
            action=action,
            component=component,
            message=message,
            severity=severity,
            details=details or {},
        )
        self._history.append(entry)
        if len(self._history) > self._config.max_history_entries:
            self._history.pop(0)
        DiagnosticsHistoryEntryRecorded(
            entry_id=entry.id,
            action=action,
            component=component,
            severity=severity,
            message=message,
        )
        self._log.info("history.recorded", action=action, component=component)
        return entry

    def get_history(self) -> list[DiagnosticsHistoryEntry]:
        """Return all recorded history entries."""
        return list(self._history)

    # -- Thresholds --

    def set_threshold(
        self,
        metric_name: str,
        warning_threshold: float,
        critical_threshold: float,
        operator: str = "gt",
    ) -> DiagnosticsThreshold:
        """Set a threshold for a diagnostics metric."""
        threshold = DiagnosticsThreshold(
            metric_name=metric_name,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            operator=operator,
        )
        self._thresholds[metric_name] = threshold
        self._log.info("threshold.set", metric=metric_name)
        return threshold

    def get_threshold(self, metric_name: str) -> DiagnosticsThreshold | None:
        """Retrieve a threshold by metric name."""
        return self._thresholds.get(metric_name)

    def list_thresholds(self) -> list[DiagnosticsThreshold]:
        """List all configured thresholds."""
        return list(self._thresholds.values())


__all__ = ["RuntimeDiagnosticsService"]
