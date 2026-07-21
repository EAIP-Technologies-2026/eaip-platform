from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class DashboardCreated(DomainEvent):
    event_type: ClassVar[str] = "observability.dashboard.created"
    dashboard_id: str
    dashboard_name: str


class DashboardUpdated(DomainEvent):
    event_type: ClassVar[str] = "observability.dashboard.updated"
    dashboard_id: str
    dashboard_name: str


class DashboardDeleted(DomainEvent):
    event_type: ClassVar[str] = "observability.dashboard.deleted"
    dashboard_id: str
    dashboard_name: str


class AlertRuleCreated(DomainEvent):
    event_type: ClassVar[str] = "observability.alert_rule.created"
    rule_id: str
    rule_name: str
    metric_name: str
    severity: str


class AlertRuleTriggered(DomainEvent):
    event_type: ClassVar[str] = "observability.alert_rule.triggered"
    alert_id: str
    rule_id: str
    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    message: str


class AlertRuleResolved(DomainEvent):
    event_type: ClassVar[str] = "observability.alert_rule.resolved"
    alert_id: str
    rule_id: str
    rule_name: str
    resolved_at: str


class SloCreated(DomainEvent):
    event_type: ClassVar[str] = "observability.slo.created"
    slo_id: str
    slo_name: str
    target_percent: float


class SloStatusChanged(DomainEvent):
    event_type: ClassVar[str] = "observability.slo.status_changed"
    slo_id: str
    slo_name: str
    previous_status: str
    new_status: str
    current_value: float


class SloViolated(DomainEvent):
    event_type: ClassVar[str] = "observability.slo.violated"
    slo_id: str
    slo_name: str
    target_value: float
    current_value: float
    burn_rate: float


class NotificationSent(DomainEvent):
    event_type: ClassVar[str] = "observability.notification.sent"
    notification_id: str
    channel_type: str
    destination: str
    subject: str


class NotificationFailed(DomainEvent):
    event_type: ClassVar[str] = "observability.notification.failed"
    notification_id: str
    channel_type: str
    destination: str
    error_message: str
    metadata: dict[str, Any] | None = None


__all__ = [
    "AlertRuleCreated",
    "AlertRuleResolved",
    "AlertRuleTriggered",
    "DashboardCreated",
    "DashboardDeleted",
    "DashboardUpdated",
    "NotificationFailed",
    "NotificationSent",
    "SloCreated",
    "SloStatusChanged",
    "SloViolated",
]
