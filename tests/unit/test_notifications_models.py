"""Tests for notification models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.notifications.models import (
    DeliveryRecord,
    Notification,
    NotificationChannel,
    NotificationConfig,
    NotificationPreference,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplate,
)


class TestNotification:
    def test_minimal(self) -> None:
        n = Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.EMAIL,
            recipients=("user@example.com",),
            subject="Hello",
        )
        assert n.status == NotificationStatus.PENDING
        assert n.priority == NotificationPriority.NORMAL
        assert n.body == ""
        assert n.template_id is None

    def test_frozen(self) -> None:
        n = Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.EMAIL,
            recipients=("a@b.com",),
            subject="S",
        )
        with pytest.raises(ValidationError):
            n.subject = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            Notification(
                id="n1",
                type="t",
                channel=NotificationChannel.EMAIL,
                recipients=("a@b.com",),
                subject="S",
                unknown=True,
            )

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        n = Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.SMS,
            priority=NotificationPriority.HIGH,
            recipients=("+1111111111",),
            subject="Urgent",
            body="Body text",
            template_id="t1",
            template_variables={"name": "test"},
            status=NotificationStatus.SENT,
            created_at=ts,
            sent_at=ts,
            delivered_at=ts,
            read_at=ts,
            metadata={"env": "prod"},
            correlation_id="corr-1",
        )
        assert n.priority == NotificationPriority.HIGH
        assert n.body == "Body text"
        assert n.template_id == "t1"
        assert n.template_variables == {"name": "test"}
        assert n.status == NotificationStatus.SENT
        assert n.sent_at == ts
        assert n.delivered_at == ts
        assert n.read_at == ts
        assert n.metadata == {"env": "prod"}
        assert n.correlation_id == "corr-1"

    def test_all_channels(self) -> None:
        for ch in NotificationChannel:
            n = Notification(id="n1", type="t", channel=ch, recipients=("a@b.com",), subject="S")
            assert n.channel == ch

    def test_all_statuses(self) -> None:
        for st in NotificationStatus:
            n = Notification(
                id="n1",
                type="t",
                channel=NotificationChannel.EMAIL,
                recipients=("a@b.com",),
                subject="S",
                status=st,
            )
            assert n.status == st

    def test_all_priorities(self) -> None:
        for pr in NotificationPriority:
            n = Notification(
                id="n1",
                type="t",
                channel=NotificationChannel.EMAIL,
                recipients=("a@b.com",),
                subject="S",
                priority=pr,
            )
            assert n.priority == pr

    def test_multiple_recipients(self) -> None:
        n = Notification(
            id="n1",
            type="t",
            channel=NotificationChannel.EMAIL,
            recipients=("a@b.com", "b@c.com"),
            subject="S",
        )
        assert len(n.recipients) == 2

    def test_default_timestamp(self) -> None:
        n = Notification(
            id="n1",
            type="t",
            channel=NotificationChannel.EMAIL,
            recipients=("a@b.com",),
            subject="S",
        )
        assert isinstance(n.created_at, datetime)


class TestNotificationTemplate:
    def test_minimal(self) -> None:
        t = NotificationTemplate(
            id="t1",
            name="Welcome",
            channel=NotificationChannel.EMAIL,
            subject_template="Hello {{name}}",
        )
        assert t.body_template == ""
        assert t.variables == ()

    def test_frozen(self) -> None:
        t = NotificationTemplate(
            id="t1", name="W", channel=NotificationChannel.EMAIL, subject_template="Hi"
        )
        with pytest.raises(ValidationError):
            t.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            NotificationTemplate(
                id="t1",
                name="W",
                channel=NotificationChannel.EMAIL,
                subject_template="Hi",
                unknown=True,
            )

    def test_full(self) -> None:
        t = NotificationTemplate(
            id="t1",
            name="Welcome",
            channel=NotificationChannel.SMS,
            subject_template="Hi {{name}}",
            body_template="Body {{code}}",
            variables=("name", "code"),
            metadata={"version": "1"},
        )
        assert t.subject_template == "Hi {{name}}"
        assert t.body_template == "Body {{code}}"
        assert t.variables == ("name", "code")
        assert t.metadata == {"version": "1"}


class TestNotificationPreference:
    def test_minimal(self) -> None:
        p = NotificationPreference(user_id="u1", channel=NotificationChannel.EMAIL)
        assert p.enabled is True
        assert p.quiet_hours_start is None
        assert p.max_daily is None

    def test_frozen(self) -> None:
        p = NotificationPreference(user_id="u1", channel=NotificationChannel.EMAIL)
        with pytest.raises(ValidationError):
            p.enabled = False

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            NotificationPreference(user_id="u1", channel=NotificationChannel.EMAIL, unknown=True)

    def test_full(self) -> None:
        p = NotificationPreference(
            user_id="u1",
            channel=NotificationChannel.SMS,
            enabled=False,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00",
            max_daily=5,
        )
        assert p.enabled is False
        assert p.quiet_hours_start == "22:00"
        assert p.quiet_hours_end == "07:00"
        assert p.max_daily == 5


class TestDeliveryRecord:
    def test_minimal(self) -> None:
        r = DeliveryRecord(
            id="r1",
            notification_id="n1",
            channel=NotificationChannel.EMAIL,
            recipient="a@b.com",
            status=NotificationStatus.SENT,
        )
        assert r.attempt == 1
        assert r.error is None
        assert r.duration_ms is None

    def test_frozen(self) -> None:
        r = DeliveryRecord(
            id="r1",
            notification_id="n1",
            channel=NotificationChannel.EMAIL,
            recipient="a@b.com",
            status=NotificationStatus.SENT,
        )
        with pytest.raises(ValidationError):
            r.attempt = 2

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DeliveryRecord(
                id="r1",
                notification_id="n1",
                channel=NotificationChannel.EMAIL,
                recipient="a@b.com",
                status=NotificationStatus.SENT,
                unknown=True,
            )

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        r = DeliveryRecord(
            id="r1",
            notification_id="n1",
            channel=NotificationChannel.EMAIL,
            recipient="a@b.com",
            status=NotificationStatus.FAILED,
            attempt=3,
            error="connection refused",
            timestamp=ts,
            duration_ms=1500.5,
            provider_response={"code": 500},
        )
        assert r.attempt == 3
        assert r.error == "connection refused"
        assert r.duration_ms == 1500.5
        assert r.provider_response == {"code": 500}


class TestNotificationConfig:
    def test_defaults(self) -> None:
        c = NotificationConfig()
        assert c.default_priority == NotificationPriority.NORMAL
        assert c.max_retries == 3
        assert c.retry_delay_seconds == 60
        assert c.enable_digest is False
        assert c.digest_interval_minutes == 60

    def test_custom(self) -> None:
        c = NotificationConfig(
            default_priority=NotificationPriority.HIGH,
            max_retries=5,
            retry_delay_seconds=120,
            enable_digest=True,
            digest_interval_minutes=30,
            channel_providers={"email": "sendgrid"},
        )
        assert c.default_priority == NotificationPriority.HIGH
        assert c.max_retries == 5
        assert c.retry_delay_seconds == 120
        assert c.enable_digest is True
        assert c.digest_interval_minutes == 30
        assert c.channel_providers == {"email": "sendgrid"}

    def test_frozen(self) -> None:
        c = NotificationConfig()
        with pytest.raises(ValidationError):
            c.max_retries = 10

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            NotificationConfig(unknown=True)
