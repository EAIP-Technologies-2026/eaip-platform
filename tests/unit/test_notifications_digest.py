"""Tests for digest service."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from eaip.notifications.digest import DigestService
from eaip.notifications.models import Notification, NotificationChannel


class TestDigestService:
    @pytest.fixture
    def service(self) -> DigestService:
        return DigestService(interval_minutes=60)

    @pytest.fixture
    def sample_notification(self) -> Notification:
        return Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.EMAIL,
            recipients=("user@example.com",),
            subject="Test",
        )

    def test_accumulate(self, service: DigestService, sample_notification: Notification) -> None:
        service.accumulate(sample_notification)
        assert service.pending_count() == 1

    def test_accumulate_grouped(
        self, service: DigestService, sample_notification: Notification
    ) -> None:
        service.accumulate(sample_notification, group_key="team-a")
        assert service.pending_count("team-a") == 1
        assert service.pending_count("default") == 0

    def test_build_digest_no_notifications(self, service: DigestService) -> None:
        digest = service.build_digest()
        assert digest is None

    def test_build_digest_single(
        self, service: DigestService, sample_notification: Notification
    ) -> None:
        service.accumulate(sample_notification)
        digest = service.build_digest()
        assert digest is not None
        assert digest.type == "digest"
        assert "1 notification(s)" in digest.body
        assert "Test" in digest.body

    def test_build_digest_multiple(self, service: DigestService) -> None:
        n1 = Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.EMAIL,
            recipients=("a@b.com",),
            subject="Alert1",
        )
        n2 = Notification(
            id="n2",
            type="reminder",
            channel=NotificationChannel.EMAIL,
            recipients=("a@b.com",),
            subject="Reminder",
        )
        service.accumulate(n1)
        service.accumulate(n2)
        digest = service.build_digest()
        assert digest is not None
        assert "2 notification(s)" in digest.body

    @pytest.mark.asyncio
    async def test_send_digest_no_sender(
        self, service: DigestService, sample_notification: Notification
    ) -> None:
        service.accumulate(sample_notification)
        count = await service.send_digest()
        assert count == 0  # no sender configured

    @pytest.mark.asyncio
    async def test_send_digest_with_sender(self, sample_notification: Notification) -> None:
        sender = AsyncMock(return_value=None)
        service = DigestService(sender=sender)
        service.accumulate(sample_notification)
        count = await service.send_digest()
        assert count == 1
        sender.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_schedule_digest_interval_not_met(
        self, service: DigestService, sample_notification: Notification
    ) -> None:
        service.accumulate(sample_notification)
        count = await service.schedule_digest()
        assert count == 0  # interval hasn't passed

    @pytest.mark.asyncio
    async def test_schedule_digest_force(
        self, service: DigestService, sample_notification: Notification
    ) -> None:
        service.accumulate(sample_notification)
        count = await service.schedule_digest(force=True)
        assert count == 0  # no sender configured

    def test_reset(self, service: DigestService, sample_notification: Notification) -> None:
        service.accumulate(sample_notification)
        service.reset()
        assert service.pending_count() == 0
