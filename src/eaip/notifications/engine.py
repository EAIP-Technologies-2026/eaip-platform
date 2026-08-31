"""Notification engine — core dispatcher for multi-channel notifications."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from eaip.logging.context import get_logger
from eaip.notifications.digest import DigestService
from eaip.notifications.events import (
    NotificationDelivered,
    NotificationFailed,
    NotificationRead,
    NotificationSent,
)
from eaip.notifications.exceptions import ChannelNotAvailableError
from eaip.notifications.models import (
    DeliveryRecord,
    Notification,
    NotificationChannel,
    NotificationConfig,
    NotificationPriority,
    NotificationStatus,
)
from eaip.notifications.preferences import PreferenceManager
from eaip.notifications.templates import TemplateService
from eaip.shared.time import utc_now


class NotificationEngine:
    """Central notification dispatcher supporting multiple channels and delivery tracking."""

    def __init__(
        self,
        config: NotificationConfig | None = None,
        template_service: TemplateService | None = None,
        preference_manager: PreferenceManager | None = None,
        digest_service: DigestService | None = None,
    ) -> None:
        self._config = config or NotificationConfig()
        self._templates = template_service or TemplateService()
        self._preferences = preference_manager or PreferenceManager()
        self._digest = digest_service
        self._notifications: dict[str, Notification] = {}
        self._delivery_records: dict[str, DeliveryRecord] = {}
        self._events: list[Any] = []
        self._log = get_logger("eaip.notifications.engine")

    @property
    def config(self) -> NotificationConfig:
        return self._config

    @property
    def templates(self) -> TemplateService:
        return self._templates

    @property
    def preferences(self) -> PreferenceManager:
        return self._preferences

    async def send(
        self,
        notification: Notification,
    ) -> Notification:
        self._notifications[notification.id] = notification
        self._log.info(
            "notification.sending",
            notification_id=notification.id,
            channel=notification.channel.value,
        )

        if not self._channel_available(notification.channel):
            error = ChannelNotAvailableError(
                f"Channel '{notification.channel.value}' is not available"
            )
            notification = self._update_status(notification.id, NotificationStatus.FAILED)
            self._record_delivery(
                notification,
                notification.recipients[0],
                NotificationStatus.FAILED,
                error=str(error),
            )
            self._events.append(
                NotificationFailed(
                    notification_id=notification.id,
                    channel=notification.channel.value,
                    recipient=notification.recipients[0],
                    error=str(error),
                    attempt=1,
                )
            )
            return notification

        sent_notification = self._update_status(
            notification.id, NotificationStatus.SENT, sent_at=utc_now()
        )
        self._events.append(
            NotificationSent(
                notification_id=notification.id,
                channel=notification.channel.value,
                recipient=notification.recipients[0],
                subject=notification.subject,
            )
        )

        for recipient in notification.recipients:
            if not self._preferences.check_channel_allowed(recipient, notification.channel):
                self._log.info(
                    "notification.skipped_preferences",
                    recipient=recipient,
                    channel=notification.channel.value,
                )
                continue

            self._record_delivery(sent_notification, recipient, NotificationStatus.DELIVERED)
            self._events.append(
                NotificationDelivered(
                    notification_id=notification.id,
                    channel=notification.channel.value,
                    recipient=recipient,
                    delivered_at=utc_now(),
                )
            )
            self._preferences.increment_daily_count(recipient, notification.channel)

        return self._update_status(
            notification.id, NotificationStatus.DELIVERED, delivered_at=utc_now()
        )

    async def send_template(
        self,
        notification_id: str,
        notification_type: str,
        channel: NotificationChannel,
        recipients: tuple[str, ...],
        template_id: str,
        variables: dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        correlation_id: str | None = None,
    ) -> Notification:
        template = self._templates.get(template_id)
        if template is None:
            raise ChannelNotAvailableError(f"Template '{template_id}' not found") from None

        subject, body = self._templates.render(template, variables)
        notification = Notification(
            id=notification_id,
            type=notification_type,
            channel=channel,
            priority=priority,
            recipients=recipients,
            subject=subject,
            body=body,
            template_id=template_id,
            template_variables=variables,
            correlation_id=correlation_id,
        )
        return await self.send(notification)

    async def send_bulk(
        self,
        notifications: list[Notification],
    ) -> list[Notification]:
        results: list[Notification] = []
        for n in notifications:
            result = await self.send(n)
            results.append(result)
        return results

    def get_status(self, notification_id: str) -> NotificationStatus | None:
        notification = self._notifications.get(notification_id)
        if notification is None:
            return None
        return notification.status

    def cancel(self, notification_id: str) -> bool:
        notification = self._notifications.get(notification_id)
        if notification is None:
            return False
        self._update_status(notification_id, NotificationStatus.FAILED)
        return True

    def list_notifications(self) -> list[Notification]:
        return list(self._notifications.values())

    def get_notification(self, notification_id: str) -> Notification | None:
        return self._notifications.get(notification_id)

    async def retry_failed(self, notification_id: str) -> Notification | None:
        notification = self._notifications.get(notification_id)
        if notification is None or notification.status is not NotificationStatus.FAILED:
            return None
        return await self.send(notification)

    def get_delivery_records(self, notification_id: str) -> list[DeliveryRecord]:
        return [r for r in self._delivery_records.values() if r.notification_id == notification_id]

    def mark_read(self, notification_id: str) -> bool:
        notification = self._notifications.get(notification_id)
        if notification is None:
            return False
        now = utc_now()
        self._update_status(notification_id, NotificationStatus.READ, read_at=now)
        self._events.append(
            NotificationRead(
                notification_id=notification_id,
                channel=notification.channel.value,
                recipient=notification.recipients[0] if notification.recipients else "",
                read_at=now,
            )
        )
        return True

    def drain_events(self) -> list[Any]:
        events = list(self._events)
        self._events.clear()
        return events

    def _channel_available(self, channel: NotificationChannel) -> bool:
        return True

    def _update_status(
        self,
        notification_id: str,
        status: NotificationStatus,
        *,
        sent_at: datetime | None = None,
        delivered_at: datetime | None = None,
        read_at: datetime | None = None,
    ) -> Notification:
        notification = self._notifications[notification_id]
        kwargs: dict[str, Any] = {
            "id": notification.id,
            "type": notification.type,
            "channel": notification.channel,
            "priority": notification.priority,
            "recipients": notification.recipients,
            "subject": notification.subject,
            "body": notification.body,
            "template_id": notification.template_id,
            "template_variables": notification.template_variables,
            "status": status,
            "created_at": notification.created_at,
            "sent_at": sent_at if sent_at is not None else notification.sent_at,
            "delivered_at": delivered_at if delivered_at is not None else notification.delivered_at,
            "read_at": read_at if read_at is not None else notification.read_at,
            "metadata": notification.metadata,
            "correlation_id": notification.correlation_id,
        }
        updated = Notification(**kwargs)
        self._notifications[notification_id] = updated
        return updated

    def _record_delivery(
        self,
        notification: Notification,
        recipient: str,
        status: NotificationStatus,
        *,
        error: str | None = None,
        duration_ms: float | None = None,
        provider_response: dict[str, Any] | None = None,
    ) -> DeliveryRecord:
        record = DeliveryRecord(
            id=str(uuid.uuid4()),
            notification_id=notification.id,
            channel=notification.channel,
            recipient=recipient,
            status=status,
            attempt=1,
            error=error,
            duration_ms=duration_ms,
            provider_response=provider_response or {},
        )
        self._delivery_records[record.id] = record
        return record


__all__ = ["NotificationEngine"]
