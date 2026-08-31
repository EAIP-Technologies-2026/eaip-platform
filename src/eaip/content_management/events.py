"""Domain events for content management."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class ContentCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.created"
    item_id: str = ""
    name: str = ""
    content_type: str = ""
    author: str = ""


class ContentUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.updated"
    item_id: str = ""
    name: str = ""
    version: str = ""
    author: str = ""


class ContentDeleted(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.deleted"
    item_id: str = ""
    name: str = ""
    author: str = ""


class ContentPublished(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.published"
    item_id: str = ""
    name: str = ""
    version: str = ""
    author: str = ""


class ContentUnpublished(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.unpublished"
    item_id: str = ""
    name: str = ""
    author: str = ""


class ContentArchived(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.archived"
    item_id: str = ""
    name: str = ""
    author: str = ""


class ContentRestored(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.restored"
    item_id: str = ""
    name: str = ""
    author: str = ""


class ContentReviewed(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.reviewed"
    item_id: str = ""
    reviewer: str = ""
    decision: str = ""


class ContentApproved(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.approved"
    item_id: str = ""
    reviewer: str = ""


class ContentRejected(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.rejected"
    item_id: str = ""
    reviewer: str = ""
    reason: str = ""


class ContentVersionCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.version.created"
    item_id: str = ""
    version: str = ""
    change_log: str = ""
    author: str = ""


class ContentScheduled(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.scheduled"
    item_id: str = ""
    schedule_id: str = ""
    publish_at: str = ""


class ContentScheduledPublished(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.scheduled.published"
    item_id: str = ""
    schedule_id: str = ""


class ContentScheduledExpired(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.scheduled.expired"
    item_id: str = ""
    schedule_id: str = ""


class ContentLocalizationAdded(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.localization.added"
    item_id: str = ""
    locale: str = ""


class ContentLocalizationUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.localization.updated"
    item_id: str = ""
    locale: str = ""


class ContentAnalyticsCollected(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.analytics.collected"
    item_id: str = ""
    views: int = 0
    unique_visitors: int = 0


class ContentSubscriptionCreated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.subscription.created"
    item_id: str = ""
    subscriber: str = ""


class ContentSubscriptionRemoved(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.subscription.removed"
    item_id: str = ""
    subscriber: str = ""


class ContentPermissionsUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.content_management.permissions.updated"
    item_id: str = ""
    principal: str = ""
    permission: str = ""


__all__ = [
    "ContentAnalyticsCollected",
    "ContentApproved",
    "ContentArchived",
    "ContentCreated",
    "ContentDeleted",
    "ContentLocalizationAdded",
    "ContentLocalizationUpdated",
    "ContentPermissionsUpdated",
    "ContentPublished",
    "ContentRejected",
    "ContentRestored",
    "ContentReviewed",
    "ContentScheduled",
    "ContentScheduledExpired",
    "ContentScheduledPublished",
    "ContentSubscriptionCreated",
    "ContentSubscriptionRemoved",
    "ContentUnpublished",
    "ContentUpdated",
    "ContentVersionCreated",
]
