"""Notification center — unified inbox with read/unread tracking, filtering, search, acknowledgement, and bulk operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from eaip.logging.context import get_logger
from eaip.notifications.events import NotificationRead, NotificationReadAll
from eaip.notifications.models import (
    Notification,
    NotificationCategory,
    NotificationChannel,
    NotificationSeverity,
    NotificationStatus,
)


@dataclass
class NotificationFilter:
    """Filter criteria for querying notifications."""

    unread_only: bool = False
    channel: NotificationChannel | None = None
    severity: NotificationSeverity | None = None
    category: NotificationCategory | None = None
    search_query: str = ""
    group_key: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


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
        severity: NotificationSeverity | None = None,
        category: NotificationCategory | None = None,
        search_query: str = "",
        group_key: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        items = list(self._inbox.get(user_id, []))
        if unread_only:
            items = [n for n in items if n.status not in (NotificationStatus.READ, NotificationStatus.ACKNOWLEDGED, NotificationStatus.DISMISSED)]
        if channel:
            items = [n for n in items if n.channel == channel]
        if severity:
            items = [n for n in items if n.severity == severity]
        if category:
            items = [n for n in items if n.category == category]
        if search_query:
            query = search_query.lower()
            items = [
                n for n in items
                if query in n.subject.lower()
                or query in n.body.lower()
                or query in n.summary.lower()
                or query in n.type.lower()
            ]
        if group_key:
            items = [n for n in items if n.group_key == group_key]
        if start_date:
            items = [n for n in items if n.created_at >= start_date]
        if end_date:
            items = [n for n in items if n.created_at <= end_date]
        return items[offset : offset + limit]

    def get_notification(self, user_id: str, notification_id: str) -> Notification | None:
        items = self._inbox.get(user_id, [])
        for n in items:
            if n.id == notification_id:
                return n
        return None

    def mark_read(self, user_id: str, notification_id: str) -> bool:
        items = self._inbox.get(user_id, [])
        for n in items:
            if n.id == notification_id and n.status not in (NotificationStatus.READ, NotificationStatus.ACKNOWLEDGED):
                updated = n.model_copy(update={"status": NotificationStatus.READ, "read_at": datetime.now()})
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
        now = datetime.now()
        for i, n in enumerate(items):
            if n.status not in (NotificationStatus.READ, NotificationStatus.ACKNOWLEDGED, NotificationStatus.DISMISSED):
                items[i] = n.model_copy(update={"status": NotificationStatus.READ, "read_at": now})
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

    def acknowledge(self, user_id: str, notification_id: str) -> bool:
        items = self._inbox.get(user_id, [])
        for n in items:
            if n.id == notification_id and n.status not in (NotificationStatus.ACKNOWLEDGED, NotificationStatus.DISMISSED):
                updated = n.model_copy(update={"status": NotificationStatus.ACKNOWLEDGED, "acknowledged_at": datetime.now()})
                idx = items.index(n)
                items[idx] = updated
                return True
        return False

    def dismiss(self, user_id: str, notification_id: str) -> bool:
        items = self._inbox.get(user_id, [])
        for n in items:
            if n.id == notification_id and n.status != NotificationStatus.DISMISSED:
                updated = n.model_copy(update={"status": NotificationStatus.DISMISSED, "dismissed_at": datetime.now()})
                idx = items.index(n)
                items[idx] = updated
                return True
        return False

    def get_unread_count(self, user_id: str) -> int:
        return sum(
            1 for n in self._inbox.get(user_id, [])
            if n.status not in (NotificationStatus.READ, NotificationStatus.ACKNOWLEDGED, NotificationStatus.DISMISSED)
        )

    def get_counts(self, user_id: str) -> dict[str, int]:
        items = self._inbox.get(user_id, [])
        total = len(items)
        unread = sum(1 for n in items if n.status not in (NotificationStatus.READ, NotificationStatus.ACKNOWLEDGED, NotificationStatus.DISMISSED))
        acknowledged = sum(1 for n in items if n.status == NotificationStatus.ACKNOWLEDGED)
        dismissed = sum(1 for n in items if n.status == NotificationStatus.DISMISSED)
        return {
            "total": total,
            "unread": unread,
            "acknowledged": acknowledged,
            "dismissed": dismissed,
        }

    def get_group_counts(self, user_id: str) -> dict[str, int]:
        items = self._inbox.get(user_id, [])
        groups: dict[str, int] = {}
        for n in items:
            key = n.group_key or "ungrouped"
            groups[key] = groups.get(key, 0) + 1
        return groups

    def get_category_counts(self, user_id: str) -> dict[str, int]:
        items = self._inbox.get(user_id, [])
        categories: dict[str, int] = {}
        for n in items:
            cat = n.category.value
            categories[cat] = categories.get(cat, 0) + 1
        return categories

    def get_severity_counts(self, user_id: str) -> dict[str, int]:
        items = self._inbox.get(user_id, [])
        severities: dict[str, int] = {}
        for n in items:
            sev = n.severity.value
            severities[sev] = severities.get(sev, 0) + 1
        return severities

    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        items = self._inbox.get(user_id, [])
        for n in items:
            if n.id == notification_id:
                items.remove(n)
                return True
        return False


__all__ = ["NotificationCenter", "NotificationFilter"]
