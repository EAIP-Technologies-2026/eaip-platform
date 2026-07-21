from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.observability.models import (
    AlertInstance,
    AlertRule,
    DashboardWidget,
    DataPoint,
    NotificationChannel,
    ObservabilityConfig,
    ObservabilityDashboard,
    ServiceLevelObjective,
    SliDefinition,
)


class TestDataPoint:
    def test_minimal(self) -> None:
        ts = datetime.now(UTC)
        dp = DataPoint(timestamp=ts, value=42.0)
        assert dp.value == 42.0
        assert dp.labels == {}

    def test_frozen(self) -> None:
        dp = DataPoint(timestamp=datetime.now(UTC), value=1.0)
        with pytest.raises(ValidationError):
            dp.value = 2.0

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DataPoint(timestamp=datetime.now(UTC), value=1.0, bad=True)


class TestDashboardWidget:
    def test_minimal(self) -> None:
        w = DashboardWidget(id="w1", type="timeseries", title="CPU Usage")
        assert w.width == 4
        assert w.height == 4
        assert w.metric_sources == ()

    def test_frozen(self) -> None:
        w = DashboardWidget(id="w1", type="gauge", title="Gauge")
        with pytest.raises(ValidationError):
            w.title = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DashboardWidget(id="w1", type="stat", title="S", bad=True)

    def test_all_types(self) -> None:
        for t in ("timeseries", "gauge", "heatmap", "table", "stat", "alert_list"):
            w = DashboardWidget(id=f"w_{t}", type=t, title=t)
            assert w.type == t

    def test_full(self) -> None:
        w = DashboardWidget(
            id="w1",
            type="timeseries",
            title="CPU",
            metric_sources=("cpu.user", "cpu.system"),
            width=8,
            height=6,
            config={"range": {"min": 0, "max": 100}},
            position={"x": 0, "y": 0},
        )
        assert w.metric_sources == ("cpu.user", "cpu.system")
        assert w.width == 8
        assert w.height == 6
        assert w.config == {"range": {"min": 0, "max": 100}}
        assert w.position == {"x": 0, "y": 0}


class TestObservabilityDashboard:
    def test_minimal(self) -> None:
        d = ObservabilityDashboard(id="d1", name="System Overview")
        assert d.description == ""
        assert d.widgets == ()
        assert d.refresh_interval_seconds == 60
        assert d.enabled is True

    def test_frozen(self) -> None:
        d = ObservabilityDashboard(id="d1", name="D1")
        with pytest.raises(ValidationError):
            d.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ObservabilityDashboard(id="d1", name="D1", bad=True)

    def test_full(self) -> None:
        w = DashboardWidget(id="w1", type="timeseries", title="CPU")
        ts = datetime.now(UTC)
        d = ObservabilityDashboard(
            id="d1",
            name="Full Dashboard",
            description="A full dashboard",
            widgets=(w,),
            refresh_interval_seconds=120,
            tags=("prod", "critical"),
            metadata={"owner": "team-a"},
            enabled=False,
            created_at=ts,
            updated_at=ts,
        )
        assert d.description == "A full dashboard"
        assert d.widgets == (w,)
        assert d.refresh_interval_seconds == 120
        assert d.tags == ("prod", "critical")
        assert d.metadata == {"owner": "team-a"}
        assert d.enabled is False
        assert d.created_at == ts
        assert d.updated_at == ts


class TestNotificationChannel:
    def test_minimal(self) -> None:
        n = NotificationChannel(id="n1", name="Email Alerts", type="email")
        assert n.enabled is True
        assert n.config == {}

    def test_frozen(self) -> None:
        n = NotificationChannel(id="n1", name="N1", type="slack")
        with pytest.raises(ValidationError):
            n.type = "email"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            NotificationChannel(id="n1", name="N1", type="webhook", bad=True)

    def test_all_types(self) -> None:
        for t in ("email", "slack", "webhook", "pagerduty"):
            n = NotificationChannel(id=f"n_{t}", name=t, type=t)
            assert n.type == t

    def test_full(self) -> None:
        n = NotificationChannel(
            id="n1",
            name="Slack Prod",
            type="slack",
            config={"webhook_url": "https://hooks.slack.com/xxx"},
            enabled=False,
            metadata={"channel": "#alerts"},
        )
        assert n.config == {"webhook_url": "https://hooks.slack.com/xxx"}
        assert n.enabled is False
        assert n.metadata == {"channel": "#alerts"}


class TestAlertRule:
    def test_minimal(self) -> None:
        r = AlertRule(
            id="r1", name="High CPU", metric_name="cpu.usage", condition="gt", threshold=90.0
        )
        assert r.severity == "warning"
        assert r.enabled is True
        assert r.evaluation_window_seconds == 300
        assert r.cooldown_seconds == 600

    def test_frozen(self) -> None:
        r = AlertRule(id="r1", name="R1", metric_name="cpu", condition="gt", threshold=90)
        with pytest.raises(ValidationError):
            r.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AlertRule(id="r1", name="R1", metric_name="cpu", condition="gt", threshold=90, bad=True)

    def test_all_conditions(self) -> None:
        for c in ("gt", "gte", "lt", "lte", "eq", "neq"):
            r = AlertRule(id=f"r_{c}", name=c, metric_name="cpu", condition=c, threshold=50)
            assert r.condition == c

    def test_all_severities(self) -> None:
        for s in ("info", "warning", "critical"):
            r = AlertRule(
                id=f"r_{s}", name=s, metric_name="cpu", condition="gt", threshold=90, severity=s
            )
            assert r.severity == s

    def test_full(self) -> None:
        r = AlertRule(
            id="r1",
            name="High CPU Alert",
            description="Triggers when CPU exceeds 90%",
            metric_name="cpu.usage",
            condition="gt",
            threshold=90.0,
            evaluation_window_seconds=600,
            evaluation_frequency_seconds=120,
            severity="critical",
            notification_channels=("n1", "n2"),
            enabled=False,
            cooldown_seconds=1800,
            tags=("prod", "critical"),
            metadata={"pagerduty_severity": "critical"},
        )
        assert r.description == "Triggers when CPU exceeds 90%"
        assert r.evaluation_window_seconds == 600
        assert r.evaluation_frequency_seconds == 120
        assert r.severity == "critical"
        assert r.notification_channels == ("n1", "n2")
        assert r.enabled is False
        assert r.cooldown_seconds == 1800
        assert r.tags == ("prod", "critical")
        assert r.metadata == {"pagerduty_severity": "critical"}


class TestAlertInstance:
    def test_minimal(self) -> None:
        a = AlertInstance(
            id="a1",
            rule_id="r1",
            rule_name="High CPU",
            metric_name="cpu.usage",
            current_value=95.0,
            threshold=90.0,
            condition="gt",
            severity="critical",
        )
        assert a.status == "firing"
        assert a.message == ""

    def test_frozen(self) -> None:
        a = AlertInstance(
            id="a1",
            rule_id="r1",
            rule_name="R1",
            metric_name="cpu",
            current_value=95,
            threshold=90,
            condition="gt",
            severity="warning",
        )
        with pytest.raises(ValidationError):
            a.status = "resolved"

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        a = AlertInstance(
            id="a1",
            rule_id="r1",
            rule_name="High CPU",
            metric_name="cpu.usage",
            current_value=95.0,
            threshold=90.0,
            condition="gt",
            severity="critical",
            message="CPU is at 95%",
            status="acknowledged",
            fired_at=ts,
            acknowledged_at=ts,
            metadata={"escalated": True},
        )
        assert a.message == "CPU is at 95%"
        assert a.status == "acknowledged"
        assert a.fired_at == ts
        assert a.acknowledged_at == ts
        assert a.resolved_at is None
        assert a.metadata == {"escalated": True}


class TestSliDefinition:
    def test_minimal(self) -> None:
        s = SliDefinition(id="sli1", name="API Latency", metric_source="http.latency")
        assert s.calculation_method == "ratio"

    def test_frozen(self) -> None:
        s = SliDefinition(id="sli1", name="S1", metric_source="m")
        with pytest.raises(ValidationError):
            s.name = "changed"

    def test_full(self) -> None:
        s = SliDefinition(
            id="sli1",
            name="API Availability",
            description="API request success rate",
            metric_source="http.requests",
            good_events_filter="status_code < 500",
            total_events_filter="status_code > 0",
            calculation_method="ratio",
            metadata={"team": "platform"},
        )
        assert s.description == "API request success rate"
        assert s.good_events_filter == "status_code < 500"
        assert s.total_events_filter == "status_code > 0"
        assert s.metadata == {"team": "platform"}


class TestServiceLevelObjective:
    def test_minimal(self) -> None:
        s = ServiceLevelObjective(id="slo1", name="API Availability", target_value=99.9)
        assert s.target_percent == 99.9
        assert s.status == "active"
        assert s.window_seconds == 604800

    def test_frozen(self) -> None:
        s = ServiceLevelObjective(id="slo1", name="S1", target_value=99.9)
        with pytest.raises(ValidationError):
            s.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ServiceLevelObjective(id="slo1", name="S1", target_value=99.9, bad=True)

    def test_all_statuses(self) -> None:
        for st in ("active", "paused", "at_risk", "violated"):
            s = ServiceLevelObjective(id=f"slo_{st}", name=st, target_value=99.9, status=st)
            assert s.status == st

    def test_full(self) -> None:
        s = ServiceLevelObjective(
            id="slo1",
            name="API SLO",
            description="API availability SLO",
            sli_definition_id="sli1",
            target_value=99.9,
            target_percent=99.5,
            window_seconds=86400,
            burn_rate_threshold=3.0,
            alert_on_burn_rate=False,
            status="at_risk",
            current_value=98.5,
            current_burn_rate=2.5,
            tags=("api", "critical"),
            metadata={"dashboard": "d1"},
        )
        assert s.description == "API availability SLO"
        assert s.sli_definition_id == "sli1"
        assert s.target_percent == 99.5
        assert s.window_seconds == 86400
        assert s.burn_rate_threshold == 3.0
        assert s.alert_on_burn_rate is False
        assert s.status == "at_risk"
        assert s.current_value == 98.5
        assert s.current_burn_rate == 2.5
        assert s.tags == ("api", "critical")
        assert s.metadata == {"dashboard": "d1"}


class TestObservabilityConfig:
    def test_defaults(self) -> None:
        c = ObservabilityConfig()
        assert c.evaluation_interval_seconds == 60
        assert c.alert_cooldown_default_seconds == 600
        assert c.dashboard_refresh_default == 60
        assert c.slo_evaluation_interval == 300
        assert c.max_alerts_per_rule == 100

    def test_custom(self) -> None:
        c = ObservabilityConfig(
            evaluation_interval_seconds=120,
            alert_cooldown_default_seconds=1800,
            dashboard_refresh_default=300,
            slo_evaluation_interval=600,
            max_alerts_per_rule=50,
        )
        assert c.evaluation_interval_seconds == 120
        assert c.alert_cooldown_default_seconds == 1800
        assert c.dashboard_refresh_default == 300
        assert c.slo_evaluation_interval == 600
        assert c.max_alerts_per_rule == 50

    def test_frozen(self) -> None:
        c = ObservabilityConfig()
        with pytest.raises(ValidationError):
            c.evaluation_interval_seconds = 999

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ObservabilityConfig(unknown=True)
