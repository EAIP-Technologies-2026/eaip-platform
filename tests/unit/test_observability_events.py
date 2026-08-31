from __future__ import annotations

from eaip.observability.events import (
    AlertRuleCreated,
    AlertRuleResolved,
    AlertRuleTriggered,
    DashboardCreated,
    DashboardDeleted,
    DashboardUpdated,
    NotificationFailed,
    NotificationSent,
    SloCreated,
    SloStatusChanged,
    SloViolated,
)


class TestDashboardEvents:
    def test_dashboard_created(self) -> None:
        ev = DashboardCreated(dashboard_id="d1", dashboard_name="Test")
        assert ev.event_type == "observability.dashboard.created"
        assert ev.dashboard_id == "d1"
        assert ev.dashboard_name == "Test"

    def test_dashboard_updated(self) -> None:
        ev = DashboardUpdated(dashboard_id="d1", dashboard_name="Test")
        assert ev.event_type == "observability.dashboard.updated"

    def test_dashboard_deleted(self) -> None:
        ev = DashboardDeleted(dashboard_id="d1", dashboard_name="Test")
        assert ev.event_type == "observability.dashboard.deleted"


class TestAlertEvents:
    def test_alert_rule_created(self) -> None:
        ev = AlertRuleCreated(
            rule_id="r1", rule_name="High CPU", metric_name="cpu", severity="critical"
        )
        assert ev.event_type == "observability.alert_rule.created"
        assert ev.severity == "critical"

    def test_alert_rule_triggered(self) -> None:
        ev = AlertRuleTriggered(
            alert_id="a1",
            rule_id="r1",
            rule_name="High CPU",
            metric_name="cpu",
            current_value=95.0,
            threshold=90.0,
            severity="critical",
            message="CPU high",
        )
        assert ev.event_type == "observability.alert_rule.triggered"
        assert ev.current_value == 95.0
        assert ev.threshold == 90.0

    def test_alert_rule_resolved(self) -> None:
        ev = AlertRuleResolved(
            alert_id="a1", rule_id="r1", rule_name="High CPU", resolved_at="2024-01-01T00:00:00"
        )
        assert ev.event_type == "observability.alert_rule.resolved"


class TestSloEvents:
    def test_slo_created(self) -> None:
        ev = SloCreated(slo_id="slo1", slo_name="API Avail", target_percent=99.9)
        assert ev.event_type == "observability.slo.created"
        assert ev.target_percent == 99.9

    def test_slo_status_changed(self) -> None:
        ev = SloStatusChanged(
            slo_id="slo1",
            slo_name="API",
            previous_status="active",
            new_status="at_risk",
            current_value=98.0,
        )
        assert ev.event_type == "observability.slo.status_changed"
        assert ev.previous_status == "active"
        assert ev.new_status == "at_risk"

    def test_slo_violated(self) -> None:
        ev = SloViolated(
            slo_id="slo1", slo_name="API", target_value=99.9, current_value=95.0, burn_rate=5.0
        )
        assert ev.event_type == "observability.slo.violated"
        assert ev.burn_rate == 5.0


class TestNotificationEvents:
    def test_notification_sent(self) -> None:
        ev = NotificationSent(
            notification_id="n1", channel_type="slack", destination="#alerts", subject="Alert"
        )
        assert ev.event_type == "observability.notification.sent"

    def test_notification_failed(self) -> None:
        ev = NotificationFailed(
            notification_id="n1",
            channel_type="email",
            destination="a@b.com",
            error_message="timeout",
        )
        assert ev.event_type == "observability.notification.failed"
        assert ev.error_message == "timeout"
