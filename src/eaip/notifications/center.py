"""Notification center — unified inbox with read/unread tracking and bulk operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.logging.context import get_logger
from eaip.notifications.events import NotificationRead, NotificationReadAll
from eaip.notifications.models import Notification, NotificationChannel, NotificationStatus


class NotificationCenter:
    def __init__(self, event_bus: Any = None) -> None:
        self._inbox: dict[str, list[Notification]] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.notifications.center")

    def deliver(self, notification: Notification) -> Notification:
        for recipient in notification.recipients:
            if recipient not in self._inbox:
                self._inbox[recipient] = []
            delivered = notification.model_copy(update={"status": NotificationStatus.DELIVERED})
            self._inbox[recipient].append(delivered)
        return notification

    def get_inbox(
        self,
        user_id: str,
        *,
        unread_only: bool = False,
        channel: NotificationChannel | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        items = list(self._inbox.get(user_id, []))
        if unread_only:
            items = [n for n in items if n.status != NotificationStatus.READ]
        if channel:
            items = [n for n in items if n.channel == channel]
        return items[offset : offset + limit]

    def mark_read(self, user_id: str, notification_id: str) -> bool:
        items = self._inbox.get(user_id, [])
        for n in items:
            if n.id == notification_id and n.status != NotificationStatus.READ:
                updated = n.model_copy(update={"status": NotificationStatus.READ})
                idx = items.index(n)
                items[idx] = updated
                if self._event_bus is not None:
                    import asyncio

                    try:
                        asyncio.ensure_future(
                            self._event_bus.publish(
                                NotificationRead(
                                    notification_id=notification_id,
                                    channel="in_app",
                                    recipient=user_id,
                                    read_at=datetime.now(),
                                )
                            )
                        )
                    except Exception:
                        pass
                return True
        return False

    def mark_all_read(self, user_id: str) -> int:
        items = self._inbox.get(user_id, [])
        count = 0
        for i, n in enumerate(items):
            if n.status != NotificationStatus.READ:
                items[i] = n.model_copy(update={"status": NotificationStatus.READ})
                count += 1
        if count > 0 and self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(
                    self._event_bus.publish(NotificationReadAll(user_id=user_id, count=count))
                )
            except Exception:
                pass
        return count

    def get_unread_count(self, user_id: str) -> int:
        return sum(1 for n in self._inbox.get(user_id, []) if n.status != NotificationStatus.READ)

    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        items = self._inbox.get(user_id, [])
        for n in items:
            if n.id == notification_id:
                items.remove(n)
                return True
        return False


__all__ = ["NotificationCenter"]
