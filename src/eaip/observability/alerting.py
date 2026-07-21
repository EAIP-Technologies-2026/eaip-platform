from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from eaip.logging.context import get_logger
from eaip.observability.events import (
    AlertRuleCreated,
    AlertRuleResolved,
    AlertRuleTriggered,
)
from eaip.observability.exceptions import AlertRuleNotFoundError
from eaip.observability.models import (
    AlertCondition,
    AlertInstance,
    AlertRule,
    ObservabilityConfig,
)
from eaip.shared.time import utc_now


class AlertService:
    name: str = "observability.alerting"

    def __init__(
        self,
        config: ObservabilityConfig | None = None,
    ) -> None:
        self._config = config or ObservabilityConfig()
        self._rules: dict[str, AlertRule] = {}
        self._alerts: dict[str, AlertInstance] = {}
        self._last_fired: dict[str, datetime] = {}
        self._log = get_logger("eaip.observability.alerting")

    def create_rule(self, rule: AlertRule) -> AlertRule:
        self._rules[rule.id] = rule
        self._log.info("alert_rule.created", id=rule.id, name=rule.name)
        AlertRuleCreated(
            rule_id=rule.id,
            rule_name=rule.name,
            metric_name=rule.metric_name,
            severity=rule.severity,
        )
        return rule

    def get_rule(self, rule_id: str) -> AlertRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise AlertRuleNotFoundError(f"Alert rule {rule_id!r} not found")
        return rule

    def update_rule(self, rule_id: str, **updates: Any) -> AlertRule:
        rule = self.get_rule(rule_id)
        updated = rule.model_copy(update=updates)
        self._rules[rule_id] = updated
        self._log.info("alert_rule.updated", id=rule_id)
        return updated

    def delete_rule(self, rule_id: str) -> None:
        self.get_rule(rule_id)
        del self._rules[rule_id]
        self._log.info("alert_rule.deleted", id=rule_id)

    def list_rules(self, enabled_only: bool = False) -> list[AlertRule]:
        result = list(self._rules.values())
        if enabled_only:
            result = [r for r in result if r.enabled]
        return result

    async def evaluate_rules(self) -> list[AlertInstance]:
        fired: list[AlertInstance] = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            alert = await self.evaluate_rule(rule.id)
            if alert is not None:
                fired.append(alert)
        self._log.info("alert_rules.evaluated", rules_fired=len(fired))
        return fired

    async def evaluate_rule(self, rule_id: str) -> AlertInstance | None:
        rule = self.get_rule(rule_id)
        if not rule.enabled:
            return None

        current_value = await self._fetch_metric_value(rule.metric_name)
        triggered = await self.check_threshold(current_value, rule.condition, rule.threshold)

        if not triggered:
            return None

        now = utc_now()
        last_fired = self._last_fired.get(rule_id)
        if last_fired and (now - last_fired).total_seconds() < rule.cooldown_seconds:
            return None

        self._last_fired[rule_id] = now
        alert = AlertInstance(
            id=str(uuid4()),
            rule_id=rule.id,
            rule_name=rule.name,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold,
            condition=rule.condition,
            severity=rule.severity,
            message=f"Alert rule {rule.name!r} triggered: {rule.metric_name} = {current_value} {rule.condition} {rule.threshold}",
            status="firing",
            fired_at=now,
        )
        self._alerts[alert.id] = alert

        AlertRuleTriggered(
            alert_id=alert.id,
            rule_id=rule.id,
            rule_name=rule.name,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold,
            severity=rule.severity,
            message=alert.message,
        )
        self._log.info("alert_rule.triggered", id=alert.id, rule_id=rule_id)
        return alert

    async def acknowledge_alert(self, alert_id: str) -> AlertInstance:
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise AlertRuleNotFoundError(f"Alert instance {alert_id!r} not found")
        updated = alert.model_copy(
            update={"status": "acknowledged", "acknowledged_at": utc_now()},
        )
        self._alerts[alert_id] = updated
        self._log.info("alert.acknowledged", id=alert_id)
        return updated

    async def resolve_alert(self, alert_id: str) -> AlertInstance:
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise AlertRuleNotFoundError(f"Alert instance {alert_id!r} not found")
        updated = alert.model_copy(
            update={"status": "resolved", "resolved_at": utc_now()},
        )
        self._alerts[alert_id] = updated

        AlertRuleResolved(
            alert_id=alert_id,
            rule_id=alert.rule_id,
            rule_name=alert.rule_name,
            resolved_at=updated.resolved_at.isoformat() if updated.resolved_at else "",
        )
        self._log.info("alert.resolved", id=alert_id)
        return updated

    async def check_threshold(
        self,
        current_value: float,
        condition: AlertCondition,
        threshold: float,
    ) -> bool:
        if condition == "gt":
            return current_value > threshold
        if condition == "gte":
            return current_value >= threshold
        if condition == "lt":
            return current_value < threshold
        if condition == "lte":
            return current_value <= threshold
        if condition == "eq":
            return abs(current_value - threshold) < 1e-9
        if condition == "neq":
            return abs(current_value - threshold) >= 1e-9
        return False  # type: ignore[unreachable]

    async def _fetch_metric_value(self, metric_name: str) -> float:
        return 0.0

    @property
    def config(self) -> ObservabilityConfig:
        return self._config

    @config.setter
    def config(self, value: ObservabilityConfig) -> None:
        self._config = value


__all__ = ["AlertService"]
