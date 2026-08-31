"""AlertCorrelator — groups related alerts, deduplicates, and suppresses noise based on rules."""

from __future__ import annotations

from eaip.alertcorr.events import AlertDeduplicated, AlertGrouped, AlertSuppressed
from eaip.alertcorr.exceptions import RuleNotFoundError
from eaip.alertcorr.models import (
    Alert,
    AlertGroup,
    AlertStatus,
    CorrelationConfig,
    CorrelationRule,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AlertCorrelator:
    """Central service for correlating, deduplicating, and suppressing alerts."""

    def __init__(self, config: CorrelationConfig | None = None) -> None:
        self._config = config or CorrelationConfig()
        self._rules: dict[str, CorrelationRule] = {}
        self._groups: dict[str, AlertGroup] = {}
        self._alerts: dict[str, Alert] = {}
        self._fingerprints: dict[str, str] = {}
        self._log = get_logger("eaip.alertcorr.correlator")

    @property
    def config(self) -> CorrelationConfig:
        return self._config

    async def register_rule(self, rule: CorrelationRule) -> CorrelationRule:
        """Register a correlation rule."""
        self._rules[rule.id] = rule
        self._log.info("alertcorr.rule.registered", rule_id=rule.id, name=rule.name)
        return rule

    async def ingest_alert(self, alert: Alert) -> Alert:
        """Ingest an alert for correlation processing."""
        self._alerts[alert.id] = alert

        if self._config.dedup_enabled:
            dup = await self._check_dedup(alert)
            if dup is not None:
                return dup

        await self._correlate(alert)

        if self._config.suppression_enabled:
            await self._check_suppression(alert)

        return alert

    async def _check_dedup(self, alert: Alert) -> Alert | None:
        """Check if the alert is a duplicate based on fingerprint."""
        if not alert.fingerprint:
            return None

        existing_id = self._fingerprints.get(alert.fingerprint)
        if existing_id is not None:
            event = AlertDeduplicated(
                alert_id=alert.id,
                original_alert_id=existing_id,
                fingerprint=alert.fingerprint,
            )
            self._log.info("alertcorr.alert.deduplicated", alert_id=alert.id, original=existing_id)
            return self._alerts[existing_id]

        self._fingerprints[alert.fingerprint] = alert.id
        return None

    async def _check_suppression(self, alert: Alert) -> bool:
        """Check if the alert should be suppressed based on rules."""
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if self._matches_criteria(alert, rule):
                suppressed = AlertStatus.SUPPRESSED
                alert = alert.model_copy(update={"status": AlertStatus.SUPPRESSED}, deep=True)
                self._alerts[alert.id] = alert
                event = AlertSuppressed(
                    alert_id=alert.id,
                    rule_id=rule.id,
                    reason=f"Suppressed by rule '{rule.name}'",
                    details={"rule_name": rule.name},
                )
                self._log.info("alertcorr.alert.suppressed", alert_id=alert.id, rule_id=rule.id)
                return True
        return False

    async def _correlate(self, alert: Alert) -> str | None:
        """Correlate an alert with existing groups based on rules."""
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if not self._matches_criteria(alert, rule):
                continue

            for gid, group in self._groups.items():
                if group.rule_id != rule.id:
                    continue
                alerts_list = list(group.alerts) + [alert]
                if len(alerts_list) > self._config.max_alerts_per_group:
                    alerts_list = alerts_list[-self._config.max_alerts_per_group :]
                updated = group.model_copy(
                    update={"alerts": tuple(alerts_list), "updated_at": utc_now()}, deep=True
                )
                self._groups[gid] = updated
                event = AlertGrouped(
                    group_id=gid,
                    rule_id=rule.id,
                    alert_ids=tuple(a.id for a in updated.alerts),
                )
                self._log.info("alertcorr.alert.grouped", alert_id=alert.id, group_id=gid)
                return gid

            group = AlertGroup(
                id=f"grp_{utc_now().timestamp():.0f}_{rule.id}",
                rule_id=rule.id,
                alerts=(alert,),
                title=f"Group for rule '{rule.name}'",
            )
            self._groups[group.id] = group
            event = AlertGrouped(
                group_id=group.id,
                rule_id=rule.id,
                alert_ids=(alert.id,),
            )
            self._log.info("alertcorr.group.created", group_id=group.id, rule_id=rule.id)
            return group.id

        return None

    async def get_rule(self, rule_id: str) -> CorrelationRule:
        """Retrieve a correlation rule by ID."""
        rule = self._rules.get(rule_id)
        if rule is None:
            raise RuleNotFoundError(f"Rule '{rule_id}' not found")
        return rule

    async def list_rules(self) -> list[CorrelationRule]:
        """List all registered correlation rules."""
        return list(self._rules.values())

    async def get_group(self, group_id: str) -> AlertGroup:
        """Retrieve an alert group by ID."""
        group = self._groups.get(group_id)
        if group is None:
            raise RuleNotFoundError(f"Group '{group_id}' not found")
        return group

    async def list_groups(self) -> list[AlertGroup]:
        """List all alert groups."""
        return list(self._groups.values())

    async def get_alert(self, alert_id: str) -> Alert:
        """Retrieve an alert by ID."""
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise RuleNotFoundError(f"Alert '{alert_id}' not found")
        return alert

    async def list_alerts(self) -> list[Alert]:
        """List all ingested alerts."""
        return list(self._alerts.values())

    def _matches_criteria(self, alert: Alert, rule: CorrelationRule) -> bool:
        """Check if an alert matches a rule's criteria."""
        for key, value in rule.match_criteria.items():
            if key == "source":
                if alert.source != value:
                    return False
            elif key == "severity":
                if alert.severity.value != value:
                    return False
            elif key == "tag":
                if value not in alert.tags:
                    return False
            elif key == "title_contains":
                if value not in alert.title:
                    return False
        return True


__all__ = ["AlertCorrelator"]
