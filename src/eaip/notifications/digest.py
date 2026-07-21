"""Digest service — accumulates notifications and sends them as a batch digest."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from eaip.logging.context import get_logger
from eaip.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationPriority,
)
from eaip.shared.time import utc_now

DigestSender = Callable[[list[Notification]], Awaitable[None]]


class DigestService:
    """Accumulates notifications and periodically sends them as digests."""

    def __init__(
        self,
        interval_minutes: int = 60,
        sender: DigestSender | None = None,
    ) -> None:
        self._interval = timedelta(minutes=interval_minutes)
        self._sender = sender
        self._pending: dict[str, list[Notification]] = {}
        self._last_send: datetime = utc_now()
        self._log = get_logger("eaip.notifications.digest")

    def accumulate(self, notification: Notification, group_key: str = "default") -> None:
        if group_key not in self._pending:
            self._pending[group_key] = []
        self._pending[group_key].append(notification)
        self._log.info(
            "notification.digest.accumulated",
            notification_id=notification.id,
            group_key=group_key,
        )

    def build_digest(self, group_key: str = "default") -> Notification | None:
        notifications = self._pending.get(group_key, [])
        if not notifications:
            return None

        recipients_map: dict[str, set[str]] = {}
        for n in notifications:
            for r in n.recipients:
                if r not in recipients_map:
                    recipients_map[r] = set()
                recipients_map[r].add(n.type)

        digest_body_lines = [f"Digest contains {len(notifications)} notification(s):"]
        for n in notifications:
            digest_body_lines.append(f"  - [{n.type}] {n.subject}")
        digest_body = "\n".join(digest_body_lines)

        return Notification(
            id=f"digest-{group_key}-{utc_now().isoformat()}",
            type="digest",
            channel=NotificationChannel.EMAIL,
            priority=NotificationPriority.NORMAL,
            recipients=tuple(recipients_map.keys()),
            subject=f"Digest: {len(notifications)} notification(s)",
            body=digest_body,
            metadata={"group_key": group_key, "source_ids": [n.id for n in notifications]},
        )

    async def send_digest(self, group_key: str = "default") -> int:
        if self._sender is None:
            self._log.warning("notification.digest.no_sender_configured")
            return 0

        notifications = self._pending.pop(group_key, [])
        if not notifications:
            return 0

        await self._sender(notifications)
        self._last_send = utc_now()
        self._log.info("notification.digest.sent", group_key=group_key, count=len(notifications))
        return len(notifications)

    async def schedule_digest(self, group_key: str = "default", force: bool = False) -> int:
        now = utc_now()
        if not force and now - self._last_send < self._interval:
            return 0
        return await self.send_digest(group_key)

    def pending_count(self, group_key: str | None = None) -> int:
        if group_key is not None:
            return len(self._pending.get(group_key, []))
        return sum(len(v) for v in self._pending.values())

    def reset(self) -> None:
        self._pending.clear()
        self._last_send = utc_now()


__all__ = ["DigestService"]
