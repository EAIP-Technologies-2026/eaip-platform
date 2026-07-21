"""Domain events for the notification orchestration runtime."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class OrchestrationRuleCreated(DomainEvent):
    """Published when an orchestration rule is created."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.rule.created"
    rule_id: str = ""
    rule_name: str = ""


class OrchestrationRuleUpdated(DomainEvent):
    """Published when an orchestration rule is updated."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.rule.updated"
    rule_id: str = ""
    rule_name: str = ""


class OrchestrationRuleDeleted(DomainEvent):
    """Published when an orchestration rule is deleted."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.rule.deleted"
    rule_id: str = ""
    rule_name: str = ""


class OrchestrationRuleActivated(DomainEvent):
    """Published when an orchestration rule is activated."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.rule.activated"
    rule_id: str = ""
    rule_name: str = ""


class OrchestrationRuleDeactivated(DomainEvent):
    """Published when an orchestration rule is deactivated."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.rule.deactivated"
    rule_id: str = ""
    rule_name: str = ""


class NotificationOrchestrated(DomainEvent):
    """Published when a notification is orchestrated against a rule."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.notification.orchestrated"
    notification_id: str = ""
    rule_id: str = ""
    channel: str = ""


class NotificationRouted(DomainEvent):
    """Published when a notification is routed through a delivery channel."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.notification.routed"
    notification_id: str = ""
    rule_id: str = ""
    route: str = ""
    channel: str = ""


class NotificationEscalated(DomainEvent):
    """Published when a notification is escalated to a higher level."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.notification.escalated"
    notification_id: str = ""
    rule_id: str = ""
    level: int = 0
    channel: str = ""


class NotificationBatchSent(DomainEvent):
    """Published when a batch of notifications is sent."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.batch.sent"
    batch_id: str = ""
    rule_id: str = ""
    count: int = 0


class DigestDelivered(DomainEvent):
    """Published when a digest is delivered to subscribers."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.digest.delivered"
    rule_id: str = ""
    rule_name: str = ""
    channel: str = ""
    item_count: int = 0


class EscalationTriggered(DomainEvent):
    """Published when an escalation is triggered for a notification."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.escalation.triggered"
    rule_id: str = ""
    rule_name: str = ""
    level: int = 0
    channel: str = ""
    targets: tuple[str, ...] = Field(default_factory=tuple)


class EscalationResolved(DomainEvent):
    """Published when an escalation is resolved."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.escalation.resolved"
    rule_id: str = ""
    rule_name: str = ""
    level: int = 0


class ScheduleTriggered(DomainEvent):
    """Published when an orchestration schedule is triggered."""

    event_type: ClassVar[str] = "eaip.notification_orchestration.schedule.triggered"
    rule_id: str = ""
    cron_expression: str = ""


NotificationOrchestrationEvent = (
    OrchestrationRuleCreated
    | OrchestrationRuleUpdated
    | OrchestrationRuleDeleted
    | OrchestrationRuleActivated
    | OrchestrationRuleDeactivated
    | NotificationOrchestrated
    | NotificationRouted
    | NotificationEscalated
    | NotificationBatchSent
    | DigestDelivered
    | EscalationTriggered
    | EscalationResolved
    | ScheduleTriggered
)

__all__ = [
    "DigestDelivered",
    "EscalationResolved",
    "EscalationTriggered",
    "NotificationBatchSent",
    "NotificationEscalated",
    "NotificationOrchestrated",
    "NotificationOrchestrationEvent",
    "NotificationRouted",
    "OrchestrationRuleActivated",
    "OrchestrationRuleCreated",
    "OrchestrationRuleDeactivated",
    "OrchestrationRuleDeleted",
    "OrchestrationRuleUpdated",
    "ScheduleTriggered",
]
