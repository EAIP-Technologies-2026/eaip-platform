"""NotificationOrchestrationService — rule management, routing, escalations, and digests."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.notification_orchestration.events import (
    EscalationResolved,
    EscalationTriggered,
    NotificationBatchSent,
    NotificationOrchestrated,
)
from eaip.notification_orchestration.exceptions import (
    NotificationRoutingError,
    OrchestrationExecutionError,
    OrchestrationRuleNotFoundError,
)
from eaip.notification_orchestration.models import (
    NotificationBatch,
    NotificationOrchestrationConfig,
    OrchestrationRule,
    OrchestrationSchedule,
    OrchestrationStatus,
)
from eaip.shared.time import utc_now


class NotificationOrchestrationService:
    """Central service for managing orchestration rules, routing, escalations, and digests."""

    def __init__(self, config: NotificationOrchestrationConfig | None = None) -> None:
        """Initialize the service with an optional config."""
        self._config = config or NotificationOrchestrationConfig()
        self._rules: dict[str, OrchestrationRule] = {}
        self._batches: dict[str, NotificationBatch] = {}
        self._log = get_logger("eaip.notification_orchestration.service")

    # -- rules ------------------------------------------------------------------

    async def create_rule(self, rule: OrchestrationRule) -> OrchestrationRule:
        """Register a new orchestration rule."""
        self._rules[rule.id] = rule
        self._log.info("orchestration.rule.created", rule_id=rule.id, rule_name=rule.name)
        return rule

    async def get_rule(self, rule_id: str) -> OrchestrationRule:
        """Retrieve a rule by its identifier."""
        rule = self._rules.get(rule_id)
        if rule is None:
            raise OrchestrationRuleNotFoundError(rule_id)
        return rule

    async def update_rule(self, rule_id: str, **updates: object) -> OrchestrationRule:
        """Update fields on an existing orchestration rule."""
        current = await self.get_rule(rule_id)
        updated = current.model_copy(update={**updates, "updated_at": utc_now()})
        self._rules[rule_id] = updated
        self._log.info("orchestration.rule.updated", rule_id=rule_id)
        return updated

    async def delete_rule(self, rule_id: str) -> None:
        """Delete an orchestration rule by its identifier."""
        if rule_id not in self._rules:
            raise OrchestrationRuleNotFoundError(rule_id)
        del self._rules[rule_id]
        self._log.info("orchestration.rule.deleted", rule_id=rule_id)

    async def list_rules(self) -> list[OrchestrationRule]:
        """Return all registered orchestration rules."""
        return list(self._rules.values())

    async def activate_rule(self, rule_id: str) -> OrchestrationRule:
        """Activate a rule, setting its status to ACTIVE."""
        return await self.update_rule(rule_id, status=OrchestrationStatus.ACTIVE)

    async def deactivate_rule(self, rule_id: str) -> OrchestrationRule:
        """Deactivate a rule, setting its status to PAUSED."""
        return await self.update_rule(rule_id, status=OrchestrationStatus.PAUSED)

    # -- routing ----------------------------------------------------------------

    async def route_notification(self, rule_id: str, notification_id: str, channel: str) -> str:
        """Route a notification through the configured delivery channel."""
        rule = await self.get_rule(rule_id)
        if not rule.enabled:
            raise OrchestrationExecutionError(f"Rule {rule_id!r} is not enabled")

        if not rule.routes:
            raise NotificationRoutingError(f"No routes defined for rule {rule_id!r}")

        primary = next((r for r in rule.routes if r.channel == channel), None)
        if primary is None:
            raise NotificationRoutingError(f"No route for channel {channel!r} in rule {rule_id!r}")

        self._log.info(
            "orchestration.notification.routed",
            notification_id=notification_id,
            rule_id=rule_id,
            channel=channel,
        )
        return primary.channel

    async def orchestrate_notification(
        self, rule_id: str, notification_id: str, channel: str
    ) -> NotificationOrchestrated:
        """Orchestrate a notification by routing it through the rule."""
        await self.route_notification(rule_id, notification_id, channel)
        return NotificationOrchestrated(
            notification_id=notification_id,
            rule_id=rule_id,
            channel=channel,
        )

    # -- escalation -------------------------------------------------------------

    async def trigger_escalation(self, rule_id: str, level: int = 1) -> EscalationTriggered:
        """Trigger an escalation for the given rule at the specified level."""
        rule = await self.get_rule(rule_id)
        if rule.escalation is None or not rule.escalation.enabled:
            raise OrchestrationExecutionError(f"No escalation policy for rule {rule_id!r}")

        escalation_level = next((lev for lev in rule.escalation.levels if lev.level == level), None)
        if escalation_level is None:
            raise OrchestrationExecutionError(
                f"Escalation level {level} not found for rule {rule_id!r}"
            )

        self._log.info(
            "orchestration.escalation.triggered",
            rule_id=rule_id,
            level=level,
        )
        return EscalationTriggered(
            rule_id=rule_id,
            rule_name=rule.name,
            level=level,
            channel=escalation_level.channels[0] if escalation_level.channels else "",
            targets=escalation_level.targets,
        )

    async def resolve_escalation(self, rule_id: str) -> EscalationResolved:
        """Resolve an active escalation for the given rule."""
        rule = await self.get_rule(rule_id)
        self._log.info("orchestration.escalation.resolved", rule_id=rule_id)
        return EscalationResolved(
            rule_id=rule_id,
            rule_name=rule.name,
            level=0,
        )

    # -- digests ----------------------------------------------------------------

    async def deliver_digest(self, rule_id: str, channel: str) -> int:
        """Deliver a digest notification for the given rule and channel."""
        rule = await self.get_rule(rule_id)
        if rule.digest is None:
            raise OrchestrationExecutionError(f"No digest config for rule {rule_id!r}")

        batch = NotificationBatch(
            id=f"batch_{rule_id}_{int(utc_now().timestamp())}",
            rule_id=rule_id,
            channel=channel,
            status=OrchestrationStatus.COMPLETED,
            sent_at=utc_now(),
        )
        self._batches[batch.id] = batch
        self._log.info(
            "orchestration.digest.delivered",
            rule_id=rule_id,
            channel=channel,
        )
        return rule.digest.max_items

    # -- batches ----------------------------------------------------------------

    async def send_batch(self, rule_id: str, count: int) -> NotificationBatchSent:
        """Send a batch of notifications for the given rule."""
        await self.get_rule(rule_id)
        batch = NotificationBatch(
            id=f"batch_{rule_id}_{int(utc_now().timestamp())}",
            rule_id=rule_id,
            status=OrchestrationStatus.COMPLETED,
            sent_at=utc_now(),
        )
        self._batches[batch.id] = batch
        self._log.info(
            "orchestration.batch.sent",
            batch_id=batch.id,
            rule_id=rule_id,
            count=count,
        )
        return NotificationBatchSent(
            batch_id=batch.id,
            rule_id=rule_id,
            count=count,
        )

    async def list_batches(self) -> list[NotificationBatch]:
        """Return all notification batches."""
        return list(self._batches.values())

    async def get_batch(self, batch_id: str) -> NotificationBatch:
        """Retrieve a batch by its identifier."""
        batch = self._batches.get(batch_id)
        if batch is None:
            raise OrchestrationRuleNotFoundError(batch_id)
        return batch

    # -- schedule ---------------------------------------------------------------

    async def trigger_schedule(self, rule_id: str) -> OrchestrationSchedule | None:
        """Trigger the schedule associated with the given rule."""
        rule = await self.get_rule(rule_id)
        return rule.schedule


__all__ = ["NotificationOrchestrationService"]
