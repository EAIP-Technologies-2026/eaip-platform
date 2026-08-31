"""Domain events for alert correlation."""

from __future__ import annotations

from typing import Any, ClassVar

from eaip.events.event import DomainEvent


class AlertGrouped(DomainEvent):
    """Emitted when alerts are grouped together."""

    event_type: ClassVar[str] = "eaip.alertcorr.alert.grouped"

    group_id: str
    rule_id: str
    alert_ids: tuple[str, ...]


class AlertDeduplicated(DomainEvent):
    """Emitted when an alert is deduplicated."""

    event_type: ClassVar[str] = "eaip.alertcorr.alert.deduplicated"

    alert_id: str
    original_alert_id: str
    fingerprint: str


class AlertSuppressed(DomainEvent):
    """Emitted when an alert is suppressed."""

    event_type: ClassVar[str] = "eaip.alertcorr.alert.suppressed"

    alert_id: str
    rule_id: str
    reason: str
    details: dict[str, Any]


__all__ = [
    "AlertDeduplicated",
    "AlertGrouped",
    "AlertSuppressed",
]
