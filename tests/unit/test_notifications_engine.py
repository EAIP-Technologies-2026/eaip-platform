"""Tests for notification engine."""

from __future__ import annotations

import pytest

from eaip.notifications.engine import NotificationEngine
from eaip.notifications.events import (
    NotificationDelivered,
    NotificationRead,
    NotificationSent,
)
from eaip.notifications.exceptions import ChannelNotAvailableError
from eaip.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationConfig,
    NotificationStatus,
    NotificationTemplate,
)


class TestNotificationEngine:
    @pytest.fixture
    def engine(self) -> NotificationEngine:
        return NotificationEngine()

    @pytest.fixture
    def sample_notification(self) -> Notification:
        return Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.EMAIL,
            recipients=("user@example.com",),
            subject="Test Alert",
        )

    @pytest.mark.asyncio
    async def test_send_notification(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        result = await engine.send(sample_notification)
        assert result.id == "n1"
        assert result.status == NotificationStatus.DELIVERED
        assert result.sent_at is not None
        assert result.delivered_at is not None

    @pytest.mark.asyncio
    async def test_send_notification_listed(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        await engine.send(sample_notification)
        assert len(engine.list_notifications()) == 1

    @pytest.mark.asyncio
    async def test_send_emits_sent_event(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        await engine.send(sample_notification)
        events = engine.drain_events()
        assert any(isinstance(e, NotificationSent) for e in events)

    @pytest.mark.asyncio
    async def test_send_emits_delivered_event(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        await engine.send(sample_notification)
        events = engine.drain_events()
        assert any(isinstance(e, NotificationDelivered) for e in events)

    @pytest.mark.asyncio
    async def test_send_template(self, engine: NotificationEngine) -> None:
        template = NotificationTemplate(
            id="t1",
            name="Welcome",
            channel=NotificationChannel.EMAIL,
            subject_template="Hello {{name}}",
            body_template="Welcome {{name}}!",
            variables=("name",),
        )
        engine._templates._templates["t1"] = template
        result = await engine.send_template(
            notification_id="n2",
            notification_type="welcome",
            channel=NotificationChannel.EMAIL,
            recipients=("user@example.com",),
            template_id="t1",
            variables={"name": "Alice"},
        )
        assert result.subject == "Hello Alice"
        assert result.body == "Welcome Alice!"
        assert result.template_id == "t1"

    @pytest.mark.asyncio
    async def test_send_template_missing(self, engine: NotificationEngine) -> None:
        with pytest.raises(ChannelNotAvailableError):
            await engine.send_template(
                notification_id="n3",
                notification_type="t",
                channel=NotificationChannel.EMAIL,
                recipients=("a@b.com",),
                template_id="nonexistent",
                variables={},
            )

    @pytest.mark.asyncio
    async def test_send_bulk(self, engine: NotificationEngine) -> None:
        notifications = [
            Notification(
                id="b1",
                type="t",
                channel=NotificationChannel.EMAIL,
                recipients=("a@b.com",),
                subject="S1",
            ),
            Notification(
                id="b2",
                type="t",
                channel=NotificationChannel.EMAIL,
                recipients=("b@b.com",),
                subject="S2",
            ),
        ]
        results = await engine.send_bulk(notifications)
        assert len(results) == 2
        assert all(r.status == NotificationStatus.DELIVERED for r in results)

    @pytest.mark.asyncio
    async def test_get_status(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        assert engine.get_status("n1") is None
        await engine.send(sample_notification)
        assert engine.get_status("n1") == NotificationStatus.DELIVERED

    def test_get_status_unknown(self, engine: NotificationEngine) -> None:
        assert engine.get_status("nonexistent") is None

    @pytest.mark.asyncio
    async def test_cancel_pending(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        engine._notifications["n1"] = sample_notification
        assert engine.cancel("n1") is True
        assert engine.get_status("n1") == NotificationStatus.FAILED

    def test_cancel_nonexistent(self, engine: NotificationEngine) -> None:
        assert engine.cancel("nonexistent") is False

    @pytest.mark.asyncio
    async def test_retry_failed(self, engine: NotificationEngine) -> None:
        n = Notification(
            id="r1",
            type="t",
            channel=NotificationChannel.EMAIL,
            recipients=("a@b.com",),
            subject="Retry",
            status=NotificationStatus.FAILED,
        )
        engine._notifications["r1"] = n
        result = await engine.retry_failed("r1")
        assert result is not None
        assert result.status == NotificationStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_retry_failed_not_failed(self, engine: NotificationEngine) -> None:
        n = Notification(
            id="r2",
            type="t",
            channel=NotificationChannel.EMAIL,
            recipients=("a@b.com",),
            subject="OK",
            status=NotificationStatus.DELIVERED,
        )
        engine._notifications["r2"] = n
        result = await engine.retry_failed("r2")
        assert result is None

    @pytest.mark.asyncio
    async def test_retry_failed_nonexistent(self, engine: NotificationEngine) -> None:
        result = await engine.retry_failed("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_read(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        engine._notifications["n1"] = sample_notification
        assert engine.mark_read("n1") is True
        n = engine.get_notification("n1")
        assert n is not None
        assert n.status == NotificationStatus.READ
        assert n.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_read_emits_event(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        engine._notifications["n1"] = sample_notification
        engine.mark_read("n1")
        events = engine.drain_events()
        assert any(isinstance(e, NotificationRead) for e in events)

    def test_mark_read_nonexistent(self, engine: NotificationEngine) -> None:
        assert engine.mark_read("nonexistent") is False

    def test_get_notification(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        engine._notifications["n1"] = sample_notification
        n = engine.get_notification("n1")
        assert n is not None
        assert n.id == "n1"

    def test_get_notification_nonexistent(self, engine: NotificationEngine) -> None:
        assert engine.get_notification("nonexistent") is None

    @pytest.mark.asyncio
    async def test_delivery_records_created(
        self, engine: NotificationEngine, sample_notification: Notification
    ) -> None:
        await engine.send(sample_notification)
        records = engine.get_delivery_records("n1")
        assert len(records) == 1
        assert records[0].notification_id == "n1"
        assert records[0].status == NotificationStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_multiple_recipients_multiple_records(self, engine: NotificationEngine) -> None:
        n = Notification(
            id="multi",
            type="t",
            channel=NotificationChannel.EMAIL,
            recipients=("a@b.com", "b@c.com"),
            subject="Multi",
        )
        await engine.send(n)
        records = engine.get_delivery_records("multi")
        assert len(records) == 2

    def test_config_defaults(self, engine: NotificationEngine) -> None:
        assert engine.config.max_retries == 3

    def test_config_custom(self) -> None:
        config = NotificationConfig(max_retries=5)
        engine = NotificationEngine(config=config)
        assert engine.config.max_retries == 5

    def test_templates_service(self, engine: NotificationEngine) -> None:
        assert engine.templates is not None

    def test_preferences_service(self, engine: NotificationEngine) -> None:
        assert engine.preferences is not None
