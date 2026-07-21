"""Multi-channel notification engine — dispatch, templates, preferences, digests, and delivery tracking."""

from __future__ import annotations

from eaip.notifications.digest import DigestService
from eaip.notifications.engine import NotificationEngine
from eaip.notifications.events import (
    NotificationDelivered,
    NotificationFailed,
    NotificationRead,
    NotificationSent,
    PreferenceUpdated,
    TemplateCreated,
    TemplateUpdated,
)
from eaip.notifications.exceptions import (
    ChannelNotAvailableError,
    DeliveryFailedError,
    NotificationError,
    PreferenceNotFoundError,
    TemplateNotFoundError,
)
from eaip.notifications.health import NotificationHealthCheck
from eaip.notifications.integration import NotificationRuntimeModule
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
from eaip.notifications.preferences import PreferenceManager
from eaip.notifications.templates import TemplateService

__all__ = [
    "ChannelNotAvailableError",
    "DeliveryFailedError",
    "DeliveryRecord",
    "DigestService",
    "Notification",
    "NotificationChannel",
    "NotificationConfig",
    "NotificationDelivered",
    "NotificationEngine",
    "NotificationError",
    "NotificationFailed",
    "NotificationHealthCheck",
    "NotificationPreference",
    "NotificationPriority",
    "NotificationRead",
    "NotificationRuntimeModule",
    "NotificationSent",
    "NotificationStatus",
    "NotificationTemplate",
    "PreferenceManager",
    "PreferenceNotFoundError",
    "PreferenceUpdated",
    "TemplateCreated",
    "TemplateNotFoundError",
    "TemplateService",
    "TemplateUpdated",
]
