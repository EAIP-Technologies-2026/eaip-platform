"""IdleResourceNotifier — track and notify on idle resources."""

from __future__ import annotations

from eaip.idlenotify.events import (
    IdleNotificationSent,
    ResourceArchived,
    ResourceMarkedIdle,
)
from eaip.idlenotify.exceptions import NotifierError, ResourceNotFoundError
from eaip.idlenotify.models import (
    IdleNotification,
    NotifierConfig,
    Resource,
    ResourceStatus,
    Severity,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class IdleResourceNotifier:
    """Central service for detecting and notifying on idle resources."""

    def __init__(self, config: NotifierConfig | None = None) -> None:
        self._config = config or NotifierConfig()
        self._resources: dict[str, Resource] = {}
        self._notifications: dict[str, IdleNotification] = {}
        self._log = get_logger("eaip.idlenotify.notifier")

    @property
    def config(self) -> NotifierConfig:
        return self._config

    async def register_resource(self, resource: Resource) -> Resource:
        """Register a resource for idle tracking."""
        self._resources[resource.id] = resource
        self._log.info(
            "idlenotify.resource.registered", resource_id=resource.id, name=resource.name
        )
        return resource

    async def get_resource(self, resource_id: str) -> Resource:
        """Get a tracked resource by ID."""
        resource = self._resources.get(resource_id)
        if resource is None:
            raise ResourceNotFoundError(f"Resource not found: {resource_id}")
        return resource

    async def list_resources(self, status: ResourceStatus | None = None) -> list[Resource]:
        """List tracked resources, optionally filtered by status."""
        result = list(self._resources.values())
        if status is not None:
            result = [r for r in result if r.status == status]
        return sorted(result, key=lambda r: r.name)

    async def update_resource_activity(self, resource_id: str) -> Resource:
        """Update the last-used timestamp for a resource."""
        resource = await self.get_resource(resource_id)
        updated = resource.model_copy(
            update={"last_used_at": utc_now(), "status": ResourceStatus.ACTIVE}
        )
        self._resources[resource_id] = updated
        self._log.info("idlenotify.resource.activity_updated", resource_id=resource_id)
        return updated

    async def evaluate_idle_resources(self) -> list[IdleNotification]:
        """Check all resources and generate notifications for idle ones."""
        now = utc_now()
        notifications: list[IdleNotification] = []

        for resource in list(self._resources.values()):
            if resource.status == ResourceStatus.ARCHIVED:
                continue

            idle_hours = (now - resource.last_used_at).total_seconds() / 3600
            threshold = resource.idle_threshold_hours

            if idle_hours < threshold:
                continue

            previous = resource.status

            if idle_hours >= threshold * 3:
                new_status = ResourceStatus.ARCHIVED
                severity = Severity.CRITICAL
                ResourceArchived(
                    resource_id=resource.id,
                    resource_name=resource.name,
                    idle_duration_hours=round(idle_hours, 2),
                )
            elif idle_hours >= threshold * 2:
                new_status = ResourceStatus.STALE
                severity = Severity.WARNING
            else:
                new_status = ResourceStatus.IDLE
                severity = Severity.INFO

            updated = resource.model_copy(update={"status": new_status})
            self._resources[resource.id] = updated

            ResourceMarkedIdle(
                resource_id=resource.id,
                resource_name=resource.name,
                previous_status=previous,
                new_status=new_status,
            )

            notification = IdleNotification(
                id=f"notif-{resource.id}-{int(now.timestamp())}",
                resource_id=resource.id,
                idle_duration=round(idle_hours, 2),
                severity=severity,
            )
            self._notifications[notification.id] = notification
            notifications.append(notification)

            IdleNotificationSent(
                notification_id=notification.id,
                resource_id=resource.id,
                severity=severity,
                idle_duration=notification.idle_duration,
            )

            self._log.info(
                "idlenotify.notification.created",
                resource_id=resource.id,
                severity=severity.value,
                idle_hours=round(idle_hours, 2),
            )

            if len(notifications) >= self._config.max_notifications_per_run:
                break

        return notifications

    async def acknowledge_notification(self, notification_id: str) -> IdleNotification:
        """Mark a notification as acknowledged."""
        notification = self._notifications.get(notification_id)
        if notification is None:
            raise NotifierError(f"Notification not found: {notification_id}")
        updated = notification.model_copy(update={"acknowledged_at": utc_now()})
        self._notifications[notification_id] = updated
        return updated

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics."""
        total = len(self._resources)
        active = sum(1 for r in self._resources.values() if r.status == ResourceStatus.ACTIVE)
        idle = sum(1 for r in self._resources.values() if r.status == ResourceStatus.IDLE)
        stale = sum(1 for r in self._resources.values() if r.status == ResourceStatus.STALE)
        archived = sum(1 for r in self._resources.values() if r.status == ResourceStatus.ARCHIVED)
        return {
            "total_resources": total,
            "active": active,
            "idle": idle,
            "stale": stale,
            "archived": archived,
            "total_notifications": len(self._notifications),
        }


__all__ = ["IdleResourceNotifier"]
