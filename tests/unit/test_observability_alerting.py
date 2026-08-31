from __future__ import annotations

import pytest

from eaip.observability.alerting import AlertService
from eaip.observability.exceptions import AlertRuleNotFoundError
from eaip.observability.models import AlertRule, ObservabilityConfig


class TestAlertService:
    def test_default_config(self) -> None:
        svc = AlertService()
        assert svc.config.evaluation_interval_seconds == 60

    def test_custom_config(self) -> None:
        config = ObservabilityConfig(max_alerts_per_rule=25)
        svc = AlertService(config=config)
        assert svc.config.max_alerts_per_rule == 25

    def test_create_and_get_rule(self) -> None:
        svc = AlertService()
        r = AlertRule(
            id="r1", name="High CPU", metric_name="cpu.usage", condition="gt", threshold=90.0
        )
        svc.create_rule(r)
        assert svc.get_rule("r1").name == "High CPU"

    def test_get_rule_not_found(self) -> None:
        svc = AlertService()
        with pytest.raises(AlertRuleNotFoundError):
            svc.get_rule("nonexistent")

    def test_update_rule(self) -> None:
        svc = AlertService()
        r = AlertRule(id="r1", name="Old", metric_name="cpu", condition="gt", threshold=90)
        svc.create_rule(r)
        svc.update_rule("r1", name="New", threshold=95.0)
        updated = svc.get_rule("r1")
        assert updated.name == "New"
        assert updated.threshold == 95.0

    def test_delete_rule(self) -> None:
        svc = AlertService()
        r = AlertRule(id="r1", name="To Delete", metric_name="cpu", condition="gt", threshold=90)
        svc.create_rule(r)
        svc.delete_rule("r1")
        with pytest.raises(AlertRuleNotFoundError):
            svc.get_rule("r1")

    def test_list_rules(self) -> None:
        svc = AlertService()
        r1 = AlertRule(
            id="r1", name="R1", metric_name="cpu", condition="gt", threshold=90, enabled=True
        )
        r2 = AlertRule(
            id="r2", name="R2", metric_name="mem", condition="lt", threshold=50, enabled=False
        )
        svc.create_rule(r1)
        svc.create_rule(r2)
        all_rules = svc.list_rules()
        assert len(all_rules) == 2
        enabled = svc.list_rules(enabled_only=True)
        assert len(enabled) == 1

    async def test_evaluate_rule_triggers(self) -> None:
        svc = AlertService()
        r = AlertRule(
            id="r1", name="Low CPU", metric_name="cpu.usage", condition="lt", threshold=10.0
        )
        svc.create_rule(r)
        alert = await svc.evaluate_rule("r1")
        assert alert is not None
        assert alert.rule_id == "r1"
        assert alert.status == "firing"
        assert alert.current_value == 0.0
        assert alert.threshold == 10.0

    async def test_evaluate_rule_does_not_trigger(self) -> None:
        svc = AlertService()
        r = AlertRule(
            id="r1", name="High CPU", metric_name="cpu.usage", condition="gt", threshold=10.0
        )
        svc.create_rule(r)
        alert = await svc.evaluate_rule("r1")
        assert alert is None

    async def test_evaluate_rules(self) -> None:
        svc = AlertService()
        r1 = AlertRule(
            id="r1", name="R1", metric_name="cpu", condition="lt", threshold=10, enabled=True
        )
        r2 = AlertRule(
            id="r2", name="R2", metric_name="mem", condition="gt", threshold=10, enabled=True
        )
        svc.create_rule(r1)
        svc.create_rule(r2)
        fired = await svc.evaluate_rules()
        assert len(fired) == 1

    async def test_cooldown_prevents_duplicate(self) -> None:
        svc = AlertService()
        r = AlertRule(
            id="r1",
            name="R1",
            metric_name="cpu",
            condition="lt",
            threshold=10,
            cooldown_seconds=600,
        )
        svc.create_rule(r)
        alert1 = await svc.evaluate_rule("r1")
        assert alert1 is not None
        alert2 = await svc.evaluate_rule("r1")
        assert alert2 is None

    async def test_acknowledge_alert(self) -> None:
        svc = AlertService()
        r = AlertRule(id="r1", name="R1", metric_name="cpu", condition="lt", threshold=10)
        svc.create_rule(r)
        alert = await svc.evaluate_rule("r1")
        assert alert is not None
        ack = await svc.acknowledge_alert(alert.id)
        assert ack.status == "acknowledged"
        assert ack.acknowledged_at is not None

    async def test_resolve_alert(self) -> None:
        svc = AlertService()
        r = AlertRule(id="r1", name="R1", metric_name="cpu", condition="lt", threshold=10)
        svc.create_rule(r)
        alert = await svc.evaluate_rule("r1")
        assert alert is not None
        resolved = await svc.resolve_alert(alert.id)
        assert resolved.status == "resolved"
        assert resolved.resolved_at is not None

    async def test_check_threshold_gt(self) -> None:
        svc = AlertService()
        assert (await svc.check_threshold(100, "gt", 90)) is True
        assert (await svc.check_threshold(90, "gt", 90)) is False

    async def test_check_threshold_gte(self) -> None:
        svc = AlertService()
        assert (await svc.check_threshold(90, "gte", 90)) is True
        assert (await svc.check_threshold(89, "gte", 90)) is False

    async def test_check_threshold_lt(self) -> None:
        svc = AlertService()
        assert (await svc.check_threshold(80, "lt", 90)) is True
        assert (await svc.check_threshold(90, "lt", 90)) is False

    async def test_check_threshold_lte(self) -> None:
        svc = AlertService()
        assert (await svc.check_threshold(90, "lte", 90)) is True
        assert (await svc.check_threshold(91, "lte", 90)) is False

    async def test_check_threshold_eq(self) -> None:
        svc = AlertService()
        assert (await svc.check_threshold(90, "eq", 90)) is True
        assert (await svc.check_threshold(91, "eq", 90)) is False

    async def test_check_threshold_neq(self) -> None:
        svc = AlertService()
        assert (await svc.check_threshold(91, "neq", 90)) is True
        assert (await svc.check_threshold(90, "neq", 90)) is False

    async def test_check_threshold_unknown_condition(self) -> None:
        svc = AlertService()
        assert (await svc.check_threshold(100, "invalid", 90)) is False

    async def test_disabled_rule_not_evaluated(self) -> None:
        svc = AlertService()
        r = AlertRule(
            id="r1", name="R1", metric_name="cpu", condition="gt", threshold=50, enabled=False
        )
        svc.create_rule(r)
        alert = await svc.evaluate_rule("r1")
        assert alert is None
