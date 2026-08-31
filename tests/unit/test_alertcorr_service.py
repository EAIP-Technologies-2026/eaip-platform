"""Tests for AlertCorrelator service."""

from __future__ import annotations

import pytest

from eaip.alertcorr.correlator import AlertCorrelator
from eaip.alertcorr.exceptions import RuleNotFoundError
from eaip.alertcorr.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    CorrelationConfig,
    CorrelationRule,
)


class TestAlertCorrelator:
    @pytest.fixture
    def correlator(self) -> AlertCorrelator:
        return AlertCorrelator()

    @pytest.fixture
    def sample_rule(self) -> CorrelationRule:
        return CorrelationRule(
            id="rule1",
            name="Match critical alerts",
            match_criteria={"severity": "critical"},
            group_window_seconds=300,
        )

    @pytest.fixture
    def critical_alert(self) -> Alert:
        return Alert(
            id="alert1",
            title="CPU overload",
            severity=AlertSeverity.CRITICAL,
            source="prometheus",
            fingerprint="fp_cpu_001",
        )

    @pytest.fixture
    def info_alert(self) -> Alert:
        return Alert(
            id="alert2",
            title="Disk usage warning",
            severity=AlertSeverity.INFO,
            source="prometheus",
            fingerprint="fp_disk_001",
        )

    class TestRegisterRule:
        async def test_register_rule(
            self, correlator: AlertCorrelator, sample_rule: CorrelationRule
        ) -> None:
            result = await correlator.register_rule(sample_rule)
            assert result.id == "rule1"
            assert result.name == "Match critical alerts"

        async def test_list_rules(
            self, correlator: AlertCorrelator, sample_rule: CorrelationRule
        ) -> None:
            await correlator.register_rule(sample_rule)
            rules = await correlator.list_rules()
            assert len(rules) == 1

    class TestIngestAlert:
        async def test_ingest_alert(
            self, correlator: AlertCorrelator, sample_rule: CorrelationRule, critical_alert: Alert
        ) -> None:
            await correlator.register_rule(sample_rule)
            result = await correlator.ingest_alert(critical_alert)
            assert result.id == "alert1"

        async def test_ingest_alert_no_rules(
            self, correlator: AlertCorrelator, critical_alert: Alert
        ) -> None:
            result = await correlator.ingest_alert(critical_alert)
            assert result.id == "alert1"

        async def test_list_alerts(
            self, correlator: AlertCorrelator, critical_alert: Alert
        ) -> None:
            await correlator.ingest_alert(critical_alert)
            alerts = await correlator.list_alerts()
            assert len(alerts) == 1

    class TestDedup:
        async def test_dedup_same_fingerprint(
            self, correlator: AlertCorrelator, sample_rule: CorrelationRule
        ) -> None:
            await correlator.register_rule(sample_rule)
            a1 = Alert(id="a1", title="Alert 1", severity=AlertSeverity.HIGH, fingerprint="fp1")
            a2 = Alert(id="a2", title="Alert 2", severity=AlertSeverity.HIGH, fingerprint="fp1")
            await correlator.ingest_alert(a1)
            result = await correlator.ingest_alert(a2)
            assert result.id == "a1"

        async def test_no_dedup_different_fingerprint(self, correlator: AlertCorrelator) -> None:
            a1 = Alert(id="a1", title="Alert 1", severity=AlertSeverity.HIGH, fingerprint="fp1")
            a2 = Alert(id="a2", title="Alert 2", severity=AlertSeverity.HIGH, fingerprint="fp2")
            await correlator.ingest_alert(a1)
            result = await correlator.ingest_alert(a2)
            assert result.id == "a2"

        async def test_no_dedup_empty_fingerprint(self, correlator: AlertCorrelator) -> None:
            a1 = Alert(id="a1", title="Alert 1", severity=AlertSeverity.HIGH)
            a2 = Alert(id="a2", title="Alert 2", severity=AlertSeverity.HIGH)
            await correlator.ingest_alert(a1)
            result = await correlator.ingest_alert(a2)
            assert result.id == "a2"

    class TestSuppression:
        async def test_suppress_matching_rule(self, correlator: AlertCorrelator) -> None:
            rule = CorrelationRule(
                id="sup1", name="Suppress info", match_criteria={"severity": "info"}
            )
            await correlator.register_rule(rule)
            alert = Alert(id="a1", title="Info message", severity=AlertSeverity.INFO)
            result = await correlator.ingest_alert(alert)
            stored = await correlator.get_alert("a1")
            assert stored.status == AlertStatus.SUPPRESSED

        async def test_no_suppress_non_matching(self, correlator: AlertCorrelator) -> None:
            rule = CorrelationRule(
                id="sup1", name="Suppress info", match_criteria={"severity": "info"}
            )
            await correlator.register_rule(rule)
            alert = Alert(id="a1", title="Critical error", severity=AlertSeverity.CRITICAL)
            result = await correlator.ingest_alert(alert)
            stored = await correlator.get_alert("a1")
            assert stored.status == AlertStatus.OPEN

    class TestCorrelation:
        async def test_group_created(
            self, correlator: AlertCorrelator, sample_rule: CorrelationRule, critical_alert: Alert
        ) -> None:
            await correlator.register_rule(sample_rule)
            await correlator.ingest_alert(critical_alert)
            groups = await correlator.list_groups()
            assert len(groups) == 1
            assert groups[0].rule_id == "rule1"

        async def test_group_reused(
            self, correlator: AlertCorrelator, sample_rule: CorrelationRule
        ) -> None:
            await correlator.register_rule(sample_rule)
            a1 = Alert(id="a1", title="Alert 1", severity=AlertSeverity.CRITICAL)
            a2 = Alert(id="a2", title="Alert 2", severity=AlertSeverity.CRITICAL)
            await correlator.ingest_alert(a1)
            await correlator.ingest_alert(a2)
            groups = await correlator.list_groups()
            assert len(groups) == 1
            assert len(groups[0].alerts) == 2

        async def test_group_per_rule(self, correlator: AlertCorrelator) -> None:
            r1 = CorrelationRule(id="r1", name="Critical", match_criteria={"severity": "critical"})
            r2 = CorrelationRule(id="r2", name="High", match_criteria={"severity": "high"})
            await correlator.register_rule(r1)
            await correlator.register_rule(r2)
            a1 = Alert(id="a1", title="Critical", severity=AlertSeverity.CRITICAL)
            a2 = Alert(id="a2", title="High", severity=AlertSeverity.HIGH)
            await correlator.ingest_alert(a1)
            await correlator.ingest_alert(a2)
            groups = await correlator.list_groups()
            assert len(groups) == 2

    class TestGetRule:
        async def test_get_rule(
            self, correlator: AlertCorrelator, sample_rule: CorrelationRule
        ) -> None:
            await correlator.register_rule(sample_rule)
            rule = await correlator.get_rule("rule1")
            assert rule.name == "Match critical alerts"

        async def test_get_rule_not_found(self, correlator: AlertCorrelator) -> None:
            with pytest.raises(RuleNotFoundError):
                await correlator.get_rule("nonexistent")

    class TestGetAlert:
        async def test_get_alert(self, correlator: AlertCorrelator, critical_alert: Alert) -> None:
            await correlator.ingest_alert(critical_alert)
            alert = await correlator.get_alert("alert1")
            assert alert.title == "CPU overload"

        async def test_get_alert_not_found(self, correlator: AlertCorrelator) -> None:
            with pytest.raises(RuleNotFoundError):
                await correlator.get_alert("nonexistent")

    class TestGetGroup:
        async def test_get_group(
            self, correlator: AlertCorrelator, sample_rule: CorrelationRule, critical_alert: Alert
        ) -> None:
            await correlator.register_rule(sample_rule)
            await correlator.ingest_alert(critical_alert)
            groups = await correlator.list_groups()
            group = await correlator.get_group(groups[0].id)
            assert group.rule_id == "rule1"

        async def test_get_group_not_found(self, correlator: AlertCorrelator) -> None:
            with pytest.raises(RuleNotFoundError):
                await correlator.get_group("nonexistent")

    class TestMatchCriteria:
        async def test_match_by_source(self, correlator: AlertCorrelator) -> None:
            rule = CorrelationRule(
                id="r1", name="Match source", match_criteria={"source": "prometheus"}
            )
            await correlator.register_rule(rule)
            alert = Alert(id="a1", title="Test", severity=AlertSeverity.MEDIUM, source="prometheus")
            await correlator.ingest_alert(alert)
            groups = await correlator.list_groups()
            assert len(groups) == 1

        async def test_match_by_tag(self, correlator: AlertCorrelator) -> None:
            rule = CorrelationRule(id="r1", name="Match tag", match_criteria={"tag": "production"})
            await correlator.register_rule(rule)
            alert = Alert(
                id="a1", title="Test", severity=AlertSeverity.MEDIUM, tags=("production",)
            )
            await correlator.ingest_alert(alert)
            groups = await correlator.list_groups()
            assert len(groups) == 1

    class TestConfig:
        def test_default_config(self) -> None:
            c = AlertCorrelator()
            assert c.config.dedup_enabled is True
            assert c.config.suppression_enabled is True

        def test_custom_config(self) -> None:
            config = CorrelationConfig(dedup_enabled=False, max_alerts_per_group=50)
            c = AlertCorrelator(config=config)
            assert c.config.dedup_enabled is False
            assert c.config.max_alerts_per_group == 50
