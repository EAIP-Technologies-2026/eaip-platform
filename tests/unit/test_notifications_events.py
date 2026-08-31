"""Tests for notification domain events."""

from __future__ import annotations

from datetime import UTC, datetime

from eaip.events.event import DomainEvent
from eaip.notifications.events import (
    NotificationDelivered,
    NotificationFailed,
    NotificationRead,
    NotificationSent,
    PreferenceUpdated,
    TemplateCreated,
    TemplateUpdated,
)


class TestNotificationSent:
    def test_event_type(self) -> None:
        event = NotificationSent(
            notification_id="n1", channel="email", recipient="a@b.com", subject="Hello"
        )
        assert event.event_type == "notification.sent"
        assert isinstance(event, DomainEvent)

    def test_fields(self) -> None:
        event = NotificationSent(
            notification_id="n1", channel="sms", recipient="+1111", subject="Alert"
        )
        assert event.notification_id == "n1"
        assert event.channel == "sms"
        assert event.recipient == "+1111"
        assert event.subject == "Alert"


class TestNotificationDelivered:
    def test_event_type(self) -> None:
        ts = datetime.now(UTC)
        event = NotificationDelivered(
            notification_id="n1", channel="email", recipient="a@b.com", delivered_at=ts
        )
        assert event.event_type == "notification.delivered"

    def test_fields(self) -> None:
        ts = datetime.now(UTC)
        event = NotificationDelivered(
            notification_id="n1", channel="push", recipient="device-1", delivered_at=ts
        )
        assert event.delivered_at == ts
        assert event.channel == "push"


class TestNotificationFailed:
    def test_event_type(self) -> None:
        event = NotificationFailed(
            notification_id="n1", channel="email", recipient="a@b.com", error="timeout", attempt=2
        )
        assert event.event_type == "notification.failed"

    def test_fields(self) -> None:
        event = NotificationFailed(
            notification_id="n1",
            channel="sms",
            recipient="+1111",
            error="provider error",
            attempt=3,
        )
        assert event.error == "provider error"
        assert event.attempt == 3


class TestNotificationRead:
    def test_event_type(self) -> None:
        ts = datetime.now(UTC)
        event = NotificationRead(notification_id="n1", channel="in_app", recipient="u1", read_at=ts)
        assert event.event_type == "notification.read"

    def test_fields(self) -> None:
        ts = datetime.now(UTC)
        event = NotificationRead(notification_id="n1", channel="in_app", recipient="u1", read_at=ts)
        assert event.read_at == ts


class TestTemplateCreated:
    def test_event_type(self) -> None:
        event = TemplateCreated(template_id="t1", name="Welcome", channel="email")
        assert event.event_type == "notification.template.created"

    def test_fields(self) -> None:
        event = TemplateCreated(template_id="t1", name="Welcome", channel="sms")
        assert event.template_id == "t1"
        assert event.name == "Welcome"
        assert event.channel == "sms"


class TestTemplateUpdated:
    def test_event_type(self) -> None:
        event = TemplateUpdated(template_id="t1", name="Greeting", channel="email")
        assert event.event_type == "notification.template.updated"


class TestPreferenceUpdated:
    def test_event_type(self) -> None:
        event = PreferenceUpdated(user_id="u1", channel="email", enabled=False)
        assert event.event_type == "notification.preference.updated"

    def test_fields(self) -> None:
        event = PreferenceUpdated(user_id="u1", channel="sms", enabled=False)
        assert event.user_id == "u1"
        assert event.enabled is False


class TestAllEventsAreDomainEvents:
    def test_all_inherit_domain_event(self) -> None:
        assert issubclass(NotificationSent, DomainEvent)
        assert issubclass(NotificationDelivered, DomainEvent)
        assert issubclass(NotificationFailed, DomainEvent)
        assert issubclass(NotificationRead, DomainEvent)
        assert issubclass(TemplateCreated, DomainEvent)
        assert issubclass(TemplateUpdated, DomainEvent)
        assert issubclass(PreferenceUpdated, DomainEvent)
