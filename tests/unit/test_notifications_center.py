from __future__ import annotations

import pytest

from eaip.notifications.center import NotificationCenter
from eaip.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
)


class TestNotificationCenter:
    def test_deliver_adds_to_inbox(self) -> None:
        center = NotificationCenter()
        notification = Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.IN_APP,
            recipients=("user1",),
            subject="test",
        )
        center.deliver(notification)
        inbox = center.get_inbox("user1")
        assert len(inbox) == 1
        assert inbox[0].status == NotificationStatus.DELIVERED

    def test_get_inbox_unread_only(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s1"
        )
        n2 = Notification(
            id="n2", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s2"
        )
        center.deliver(n1)
        center.deliver(n2)
        center.mark_read("u1", "n1")
        unread = center.get_inbox("u1", unread_only=True)
        assert len(unread) == 1
        assert unread[0].id == "n2"

    def test_mark_read(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        result = center.mark_read("u1", "n1")
        assert result is True
        assert center.get_unread_count("u1") == 0

    def test_mark_read_nonexistent(self) -> None:
        center = NotificationCenter()
        result = center.mark_read("u1", "nonexistent")
        assert result is False

    def test_mark_all_read(self) -> None:
        center = NotificationCenter()
        for i in range(3):
            n = Notification(
                id=f"n{i}",
                type="a",
                channel=NotificationChannel.IN_APP,
                recipients=("u1",),
                subject=f"s{i}",
            )
            center.deliver(n)
        count = center.mark_all_read("u1")
        assert count == 3
        assert center.get_unread_count("u1") == 0

    def test_get_unread_count(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        assert center.get_unread_count("u1") == 1
        center.mark_read("u1", "n1")
        assert center.get_unread_count("u1") == 0

    def test_delete_notification(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        result = center.delete_notification("u1", "n1")
        assert result is True
        assert len(center.get_inbox("u1")) == 0

    def test_get_inbox_with_channel_filter(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s1"
        )
        n2 = Notification(
            id="n2", type="a", channel=NotificationChannel.EMAIL, recipients=("u1",), subject="s2"
        )
        center.deliver(n1)
        center.deliver(n2)
        email = center.get_inbox("u1", channel=NotificationChannel.EMAIL)
        assert len(email) == 1
        assert email[0].id == "n2"
