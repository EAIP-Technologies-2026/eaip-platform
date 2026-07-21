"""Domain events for the notification engine."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from eaip.events.event import DomainEvent


class NotificationSent(DomainEvent):
    event_type: ClassVar[str] = "notification.sent"
    notification_id: str
    channel: str
    recipient: str
    subject: str


class NotificationDelivered(DomainEvent):
    event_type: ClassVar[str] = "notification.delivered"
    notification_id: str
    channel: str
    recipient: str
    delivered_at: datetime


class NotificationFailed(DomainEvent):
    event_type: ClassVar[str] = "notification.failed"
    notification_id: str
    channel: str
    recipient: str
    error: str
    attempt: int


class NotificationRead(DomainEvent):
    event_type: ClassVar[str] = "notification.read"
    notification_id: str
    channel: str
    recipient: str
    read_at: datetime


class NotificationReadAll(DomainEvent):
    event_type: ClassVar[str] = "notification.read.all"
    user_id: str
    count: int


class TemplateCreated(DomainEvent):
    event_type: ClassVar[str] = "notification.template.created"
    template_id: str
    name: str
    channel: str


class TemplateUpdated(DomainEvent):
    event_type: ClassVar[str] = "notification.template.updated"
    template_id: str
    name: str
    channel: str


class PreferenceUpdated(DomainEvent):
    event_type: ClassVar[str] = "notification.preference.updated"
    user_id: str
    channel: str
    enabled: bool


__all__ = [
    "NotificationDelivered",
    "NotificationFailed",
    "NotificationRead",
    "NotificationReadAll",
    "NotificationSent",
    "PreferenceUpdated",
    "TemplateCreated",
    "TemplateUpdated",
]
