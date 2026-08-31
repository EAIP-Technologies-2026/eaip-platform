"""Tests for the workflow_monitoring package."""

from __future__ import annotations

from datetime import timedelta

import pytest

from eaip.shared.time import utc_now
from eaip.workflow_monitoring.events import (
    WorkflowMonitorActivated,
    WorkflowMonitorAlertResolved,
    WorkflowMonitorAlertTriggered,
    WorkflowMonitorCreated,
    WorkflowMonitorDeactivated,
    WorkflowMonitorDeleted,
    WorkflowMonitorReportGenerated,
    WorkflowMonitorSnapshotTaken,
    WorkflowMonitorStatusChanged,
    WorkflowMonitorThresholdBreached,
    WorkflowMonitorUpdated,
)
from eaip.workflow_monitoring.exceptions import (
    WorkflowMonitorAlertError,
    WorkflowMonitorConfigError,
    WorkflowMonitorDashboardError,
    WorkflowMonitorError,
    WorkflowMonitorNotFoundError,
)
from eaip.workflow_monitoring.health import WorkflowMonitorHealthCheck
from eaip.workflow_monitoring.models import (
    AlertSeverity,
    MonitorMetricPoint,
    MonitorNotificationChannel,
    MonitorThreshold,
    MonitorTimeSeries,
    WorkflowMonitorAlert,
    WorkflowMonitorConfig,
    WorkflowMonitorDashboard,
    WorkflowMonitorSnapshot,
    WorkflowMonitorStatus,
)
from eaip.workflow_monitoring.service import WorkflowMonitorService

# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def service() -> WorkflowMonitorService:
    return WorkflowMonitorService()


@pytest.fixture
def config() -> WorkflowMonitorConfig:
    return WorkflowMonitorConfig(
        id="cfg-1",
        workflow_name="order_processing",
        thresholds=(
            MonitorThreshold(
                id="th-1",
                metric_name="error_rate",
                operator="gt",
                value=0.05,
                severity=AlertSeverity.HIGH,
            ),
        ),
        notification_channels=(
            MonitorNotificationChannel(id="ch-1", type="email", target="ops@example.com"),
        ),
    )


@pytest.fixture
def dashboard() -> WorkflowMonitorDashboard:
    return WorkflowMonitorDashboard(
        id="db-1",
        name="Order Processing Dashboard",
        config_ids=("cfg-1",),
    )


# -- Model tests ---------------------------------------------------------------


class TestModels:
    def test_monitor_metric_point(self) -> None:
        now = utc_now()
        p = MonitorMetricPoint(timestamp=now, value=42.5, source="test")
        assert p.value == 42.5
        assert p.source == "test"

    def test_monitor_time_series(self) -> None:
        now = utc_now()
        ts = MonitorTimeSeries(
            metric_name="error_rate",
            points=(),
            start_time=now,
            end_time=now + timedelta(seconds=60),
        )
        assert ts.metric_name == "error_rate"
        assert ts.interval_seconds == 60.0

    def test_monitor_threshold(self) -> None:
        t = MonitorThreshold(id="t1", metric_name="latency", operator="lt", value=200.0)
        assert t.operator == "lt"
        assert t.enabled is True

    def test_monitor_notification_channel(self) -> None:
        ch = MonitorNotificationChannel(id="c1", type="slack", target="#ops")
        assert ch.type == "slack"
        assert ch.enabled is True

    def test_workflow_monitor_config_frozen(self) -> None:
        cfg = WorkflowMonitorConfig(id="c1", workflow_name="test")
        with pytest.raises(AttributeError):
            cfg.id = "c2"  # type: ignore[misc]

    def test_workflow_monitor_config_extra_forbid(self) -> None:
        with pytest.raises(ValueError):
            WorkflowMonitorConfig(
                id="c1",
                workflow_name="test",
                unknown_field="x",  # type: ignore[call-arg]
            )

    def test_alert_severity_values(self) -> None:
        assert AlertSeverity.CRITICAL.value == "critical"
        assert AlertSeverity.INFO.value == "info"

    def test_workflow_monitor_status_values(self) -> None:
        assert WorkflowMonitorStatus.ACTIVE.value == "active"
        assert WorkflowMonitorStatus.ARCHIVED.value == "archived"

    def test_workflow_monitor_alert(self) -> None:
        alert = WorkflowMonitorAlert(
            id="a1",
            config_id="cfg-1",
            severity=AlertSeverity.CRITICAL,
            metric_name="error_rate",
        )
        assert alert.acknowledged is False
        assert alert.resolved_at is None

    def test_workflow_monitor_snapshot(self) -> None:
        snap = WorkflowMonitorSnapshot(id="s1", config_id="cfg-1", healthy=True)
        assert snap.status is WorkflowMonitorStatus.ACTIVE

    def test_workflow_monitor_dashboard(self) -> None:
        db = WorkflowMonitorDashboard(id="d1", name="Test Dashboard")
        assert db.refresh_interval_seconds == 60.0


# -- Event tests ---------------------------------------------------------------


class TestEvents:
    def test_workflow_monitor_created_event_type(self) -> None:
        e = WorkflowMonitorCreated(config_id="cfg-1", workflow_name="order_processing")
        assert e.event_type == "eaip.workflow_monitoring.created"

    def test_workflow_monitor_alert_triggered(self) -> None:
        e = WorkflowMonitorAlertTriggered(
            alert_id="a1",
            config_id="cfg-1",
            severity="high",
            metric_name="error_rate",
            current_value=0.1,
            threshold_value=0.05,
        )
        assert e.event_type == "eaip.workflow_monitoring.alert.triggered"

    def test_workflow_monitor_alert_resolved(self) -> None:
        e = WorkflowMonitorAlertResolved(alert_id="a1", config_id="cfg-1")
        assert e.event_type == "eaip.workflow_monitoring.alert.resolved"

    def test_workflow_monitor_snapshot_taken(self) -> None:
        e = WorkflowMonitorSnapshotTaken(snapshot_id="s1", config_id="cfg-1", status="active")
        assert e.event_type == "eaip.workflow_monitoring.snapshot.taken"

    def test_workflow_monitor_threshold_breached(self) -> None:
        e = WorkflowMonitorThresholdBreached(
            threshold_id="th-1",
            config_id="cfg-1",
            metric_name="error_rate",
            current_value=0.1,
            threshold_value=0.05,
            severity="high",
        )
        assert e.event_type == "eaip.workflow_monitoring.threshold.breached"

    def test_workflow_monitor_status_changed(self) -> None:
        e = WorkflowMonitorStatusChanged(
            config_id="cfg-1", previous_status="active", current_status="paused"
        )
        assert e.event_type == "eaip.workflow_monitoring.status.changed"

    def test_workflow_monitor_updated(self) -> None:
        e = WorkflowMonitorUpdated(config_id="cfg-1", changes={"description": "new desc"})
        assert e.event_type == "eaip.workflow_monitoring.updated"

    def test_workflow_monitor_deleted(self) -> None:
        e = WorkflowMonitorDeleted(config_id="cfg-1", workflow_name="order_processing")
        assert e.event_type == "eaip.workflow_monitoring.deleted"

    def test_workflow_monitor_activated(self) -> None:
        e = WorkflowMonitorActivated(config_id="cfg-1", workflow_name="order_processing")
        assert e.event_type == "eaip.workflow_monitoring.activated"

    def test_workflow_monitor_deactivated(self) -> None:
        e = WorkflowMonitorDeactivated(config_id="cfg-1", workflow_name="order_processing")
        assert e.event_type == "eaip.workflow_monitoring.deactivated"

    def test_workflow_monitor_report_generated(self) -> None:
        e = WorkflowMonitorReportGenerated(report_id="r1", config_ids=("cfg-1",))
        assert e.event_type == "eaip.workflow_monitoring.report.generated"


# -- Exception tests -----------------------------------------------------------


class TestExceptions:
    def test_workflow_monitor_error(self) -> None:
        exc = WorkflowMonitorError("something went wrong")
        assert "something went wrong" in str(exc)

    def test_workflow_monitor_config_error(self) -> None:
        exc = WorkflowMonitorConfigError("invalid config")
        assert "invalid config" in str(exc)

    def test_workflow_monitor_not_found_error(self) -> None:
        exc = WorkflowMonitorNotFoundError("cfg-1")
        assert "cfg-1" in str(exc)
        assert exc.config_id == "cfg-1"

    def test_workflow_monitor_alert_error(self) -> None:
        exc = WorkflowMonitorAlertError("alert failure")
        assert "alert failure" in str(exc)

    def test_workflow_monitor_dashboard_error(self) -> None:
        exc = WorkflowMonitorDashboardError("db-1")
        assert "db-1" in str(exc)
        assert exc.dashboard_id == "db-1"


# -- Service tests -------------------------------------------------------------


class TestWorkflowMonitorService:
    async def test_create_config(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        result = await service.create_config(config)
        assert result.id == "cfg-1"

    async def test_create_config_duplicate(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        with pytest.raises(WorkflowMonitorConfigError):
            await service.create_config(config)

    async def test_get_config_not_found(self, service: WorkflowMonitorService) -> None:
        with pytest.raises(WorkflowMonitorNotFoundError):
            await service.get_config("nonexistent")

    async def test_update_config(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        updated = await service.update_config("cfg-1", description="updated desc")
        assert updated.description == "updated desc"

    async def test_delete_config(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        await service.delete_config("cfg-1")
        assert await service.list_configs() == []

    async def test_delete_config_not_found(self, service: WorkflowMonitorService) -> None:
        with pytest.raises(WorkflowMonitorNotFoundError):
            await service.delete_config("nonexistent")

    async def test_list_configs_filter_by_status(self, service: WorkflowMonitorService) -> None:
        c1 = WorkflowMonitorConfig(id="c1", workflow_name="w1", status=WorkflowMonitorStatus.ACTIVE)
        c2 = WorkflowMonitorConfig(id="c2", workflow_name="w2", status=WorkflowMonitorStatus.PAUSED)
        await service.create_config(c1)
        await service.create_config(c2)
        result = await service.list_configs(status=WorkflowMonitorStatus.ACTIVE)
        assert len(result) == 1
        assert result[0].id == "c1"

    async def test_evaluate_alerts_triggered(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        alerts = await service.evaluate_alerts("cfg-1", {"error_rate": 0.1})
        assert len(alerts) == 1
        assert alerts[0].metric_name == "error_rate"
        assert alerts[0].current_value == 0.1

    async def test_evaluate_alerts_not_triggered(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        alerts = await service.evaluate_alerts("cfg-1", {"error_rate": 0.01})
        assert len(alerts) == 0

    async def test_resolve_alert(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        alerts = await service.evaluate_alerts("cfg-1", {"error_rate": 0.1})
        alert_id = alerts[0].id
        resolved = await service.resolve_alert(alert_id)
        assert resolved.resolved_at is not None

    async def test_resolve_alert_not_found(self, service: WorkflowMonitorService) -> None:
        with pytest.raises(WorkflowMonitorAlertError):
            await service.resolve_alert("nonexistent")

    async def test_take_snapshot(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        snap = await service.take_snapshot("cfg-1", {"error_rate": 0.02})
        assert snap.config_id == "cfg-1"
        assert snap.metrics == {"error_rate": 0.02}

    async def test_create_dashboard(
        self, service: WorkflowMonitorService, dashboard: WorkflowMonitorDashboard
    ) -> None:
        result = await service.create_dashboard(dashboard)
        assert result.id == "db-1"

    async def test_create_dashboard_duplicate(
        self, service: WorkflowMonitorService, dashboard: WorkflowMonitorDashboard
    ) -> None:
        await service.create_dashboard(dashboard)
        with pytest.raises(WorkflowMonitorDashboardError):
            await service.create_dashboard(dashboard)

    async def test_get_dashboard_not_found(self, service: WorkflowMonitorService) -> None:
        with pytest.raises(WorkflowMonitorDashboardError):
            await service.get_dashboard("nonexistent")

    async def test_delete_dashboard(
        self, service: WorkflowMonitorService, dashboard: WorkflowMonitorDashboard
    ) -> None:
        await service.create_dashboard(dashboard)
        await service.delete_dashboard("db-1")
        assert await service.list_dashboards() == []

    async def test_list_alerts_unresolved_only(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        await service.evaluate_alerts("cfg-1", {"error_rate": 0.1})
        unresolved = await service.list_alerts(unresolved_only=True)
        assert len(unresolved) == 1

    async def test_health_check_degraded_when_no_configs(
        self, service: WorkflowMonitorService
    ) -> None:
        health = WorkflowMonitorHealthCheck(service=service)
        report = await health.check()
        assert report.status.value == "degraded"

    async def test_health_check_healthy(
        self, service: WorkflowMonitorService, config: WorkflowMonitorConfig
    ) -> None:
        await service.create_config(config)
        health = WorkflowMonitorHealthCheck(service=service)
        report = await health.check()
        assert report.status.value == "healthy"


# -- Integration test ----------------------------------------------------------


class TestIntegration:
    async def test_workflow_monitor_event_union(self) -> None:
        events = [
            WorkflowMonitorCreated(config_id="c1", workflow_name="w1"),
            WorkflowMonitorAlertTriggered(
                alert_id="a1",
                config_id="c1",
                severity="high",
                metric_name="m1",
                current_value=1.0,
                threshold_value=0.5,
            ),
        ]
        for event in events:
            assert "eaip.workflow_monitoring" in event.event_type
