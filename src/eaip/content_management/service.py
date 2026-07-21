"""ContentManagementService — CRUD, publish, review, schedule, localize, analytics."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from eaip.content_management.events import (
    ContentAnalyticsCollected,
    ContentApproved,
    ContentArchived,
    ContentCreated,
    ContentDeleted,
    ContentLocalizationAdded,
    ContentLocalizationUpdated,
    ContentPermissionsUpdated,
    ContentPublished,
    ContentRejected,
    ContentRestored,
    ContentReviewed,
    ContentScheduled,
    ContentScheduledExpired,
    ContentScheduledPublished,
    ContentSubscriptionCreated,
    ContentSubscriptionRemoved,
    ContentUnpublished,
    ContentUpdated,
    ContentVersionCreated,
)
from eaip.content_management.exceptions import (
    ContentLocalizationError,
    ContentNotFoundError,
    ContentPublishError,
    ContentSchedulingError,
    ContentValidationError,
    ContentVersionError,
)
from eaip.content_management.models import (
    ContentAnalytics,
    ContentCollection,
    ContentItem,
    ContentLocalization,
    ContentPermission,
    ContentPublishSchedule,
    ContentReview,
    ContentStatus,
    ContentSubscription,
    ContentVersion,
    ReviewDecision,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ContentManagementService:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._items: dict[str, ContentItem] = {}
        self._versions: dict[str, list[ContentVersion]] = defaultdict(list)
        self._reviews: dict[str, list[ContentReview]] = defaultdict(list)
        self._schedules: dict[str, ContentPublishSchedule] = {}
        self._localizations: dict[str, list[ContentLocalization]] = defaultdict(list)
        self._analytics: dict[str, list[ContentAnalytics]] = defaultdict(list)
        self._permissions: dict[str, list[ContentPermission]] = defaultdict(list)
        self._subscriptions: dict[str, list[ContentSubscription]] = defaultdict(list)
        self._collections: dict[str, ContentCollection] = {}
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.content_management.service")

    async def create_item(self, item: ContentItem) -> ContentItem:
        if item.id in self._items:
            raise ContentValidationError(f"item already exists: {item.id!r}")
        self._items[item.id] = item
        await self._event_bus.publish(
            ContentCreated(
                item_id=item.id,
                name=item.name,
                content_type=item.type.value,
                author=item.author,
            )
        )
        self._log.info("content.item.created", item_id=item.id)
        return item

    async def get_item(self, item_id: str) -> ContentItem:
        item = self._items.get(item_id)
        if item is None:
            raise ContentNotFoundError(item_id)
        return item

    async def update_item(
        self,
        item_id: str,
        body: str | None = None,
        status: ContentStatus | None = None,
    ) -> ContentItem:
        existing = await self.get_item(item_id)
        kwargs: dict[str, Any] = {"id": item_id, "name": existing.name, "type": existing.type}
        kwargs["body"] = body if body is not None else existing.body
        kwargs["status"] = status if status is not None else existing.status
        kwargs["version"] = existing.version
        kwargs["tags"] = existing.tags
        kwargs["metadata"] = existing.metadata
        kwargs["created_at"] = existing.created_at
        kwargs["updated_at"] = utc_now()
        kwargs["author"] = existing.author
        updated = ContentItem(**kwargs)
        self._items[item_id] = updated
        await self._event_bus.publish(
            ContentUpdated(
                item_id=item_id,
                name=updated.name,
                version=updated.version,
                author=updated.author,
            )
        )
        self._log.info("content.item.updated", item_id=item_id)
        return updated

    async def delete_item(self, item_id: str) -> None:
        item = await self.get_item(item_id)
        del self._items[item_id]
        self._versions.pop(item_id, None)
        self._reviews.pop(item_id, None)
        self._schedules.pop(item_id, None)
        self._localizations.pop(item_id, None)
        self._analytics.pop(item_id, None)
        self._permissions.pop(item_id, None)
        self._subscriptions.pop(item_id, None)
        await self._event_bus.publish(
            ContentDeleted(item_id=item_id, name=item.name, author=item.author)
        )
        self._log.info("content.item.deleted", item_id=item_id)

    async def list_items(self, status: ContentStatus | None = None) -> list[ContentItem]:
        items = list(self._items.values())
        if status is not None:
            items = [i for i in items if i.status == status]
        return items

    async def publish_item(self, item_id: str, author: str = "") -> ContentItem:
        item = await self.get_item(item_id)
        if item.status not in (ContentStatus.APPROVED, ContentStatus.DRAFT, ContentStatus.REVIEW):
            raise ContentPublishError(item_id, f"cannot publish from status {item.status.value}")
        updated = await self.update_item(item_id, status=ContentStatus.PUBLISHED)
        updated = updated.__class__(
            id=updated.id,
            name=updated.name,
            type=updated.type,
            body=updated.body,
            version=updated.version,
            status=ContentStatus.PUBLISHED,
            tags=updated.tags,
            metadata=updated.metadata,
            created_at=updated.created_at,
            updated_at=utc_now(),
            published_at=utc_now(),
            author=updated.author,
        )
        self._items[item_id] = updated
        await self._event_bus.publish(
            ContentPublished(
                item_id=item_id,
                name=updated.name,
                version=updated.version,
                author=author or updated.author,
            )
        )
        self._log.info("content.item.published", item_id=item_id)
        return updated

    async def unpublish_item(self, item_id: str, author: str = "") -> ContentItem:
        await self.get_item(item_id)
        updated = await self.update_item(item_id, status=ContentStatus.UNPUBLISHED)
        updated = updated.__class__(
            id=updated.id,
            name=updated.name,
            type=updated.type,
            body=updated.body,
            version=updated.version,
            status=ContentStatus.UNPUBLISHED,
            tags=updated.tags,
            metadata=updated.metadata,
            created_at=updated.created_at,
            updated_at=utc_now(),
            published_at=None,
            author=updated.author,
        )
        self._items[item_id] = updated
        await self._event_bus.publish(
            ContentUnpublished(item_id=item_id, name=updated.name, author=author or updated.author)
        )
        self._log.info("content.item.unpublished", item_id=item_id)
        return updated

    async def archive_item(self, item_id: str, author: str = "") -> ContentItem:
        await self.get_item(item_id)
        updated = await self.update_item(item_id, status=ContentStatus.ARCHIVED)
        updated = updated.__class__(
            id=updated.id,
            name=updated.name,
            type=updated.type,
            body=updated.body,
            version=updated.version,
            status=ContentStatus.ARCHIVED,
            tags=updated.tags,
            metadata=updated.metadata,
            created_at=updated.created_at,
            updated_at=utc_now(),
            published_at=None,
            author=updated.author,
        )
        self._items[item_id] = updated
        await self._event_bus.publish(
            ContentArchived(item_id=item_id, name=updated.name, author=author or updated.author)
        )
        self._log.info("content.item.archived", item_id=item_id)
        return updated

    async def restore_item(self, item_id: str, author: str = "") -> ContentItem:
        await self.get_item(item_id)
        updated = await self.update_item(item_id, status=ContentStatus.DRAFT)
        updated = updated.__class__(
            id=updated.id,
            name=updated.name,
            type=updated.type,
            body=updated.body,
            version=updated.version,
            status=ContentStatus.DRAFT,
            tags=updated.tags,
            metadata=updated.metadata,
            created_at=updated.created_at,
            updated_at=utc_now(),
            published_at=None,
            author=updated.author,
        )
        self._items[item_id] = updated
        await self._event_bus.publish(
            ContentRestored(item_id=item_id, name=updated.name, author=author or updated.author)
        )
        self._log.info("content.item.restored", item_id=item_id)
        return updated

    async def create_version(self, item_id: str, version: ContentVersion) -> ContentVersion:
        await self.get_item(item_id)
        self._versions[item_id].append(version)
        await self._event_bus.publish(
            ContentVersionCreated(
                item_id=item_id,
                version=version.version,
                change_log=version.change_log,
                author=version.author,
            )
        )
        self._log.info("content.version.created", item_id=item_id, version=version.version)
        return version

    async def list_versions(self, item_id: str) -> list[ContentVersion]:
        await self.get_item(item_id)
        return list(self._versions.get(item_id, []))

    async def get_version(self, item_id: str, version: str) -> ContentVersion:
        await self.get_item(item_id)
        for v in self._versions.get(item_id, []):
            if v.version == version:
                return v
        raise ContentVersionError(item_id, f"version {version!r} not found")

    async def review_item(self, item_id: str, review: ContentReview) -> ContentReview:
        await self.get_item(item_id)
        self._reviews[item_id].append(review)
        await self._event_bus.publish(
            ContentReviewed(
                item_id=item_id,
                reviewer=review.reviewer,
                decision=review.decision.value,
            )
        )
        if review.decision == ReviewDecision.APPROVED:
            await self.update_item(item_id, status=ContentStatus.APPROVED)
            updated = self._items[item_id]
            self._items[item_id] = updated.__class__(
                id=updated.id,
                name=updated.name,
                type=updated.type,
                body=updated.body,
                version=updated.version,
                status=ContentStatus.APPROVED,
                tags=updated.tags,
                metadata=updated.metadata,
                created_at=updated.created_at,
                updated_at=utc_now(),
                published_at=updated.published_at,
                author=updated.author,
            )
            await self._event_bus.publish(
                ContentApproved(item_id=item_id, reviewer=review.reviewer)
            )
        elif review.decision == ReviewDecision.REJECTED:
            await self._event_bus.publish(
                ContentRejected(item_id=item_id, reviewer=review.reviewer, reason=review.comments)
            )
        self._log.info("content.item.reviewed", item_id=item_id, decision=review.decision.value)
        return review

    async def get_reviews(self, item_id: str) -> list[ContentReview]:
        await self.get_item(item_id)
        return list(self._reviews.get(item_id, []))

    async def schedule_publish(self, schedule: ContentPublishSchedule) -> ContentPublishSchedule:
        await self.get_item(schedule.item_id)
        self._schedules[schedule.item_id] = schedule
        await self._event_bus.publish(
            ContentScheduled(
                item_id=schedule.item_id,
                schedule_id=schedule.id,
                publish_at=schedule.publish_at.isoformat(),
            )
        )
        self._log.info("content.schedule.created", item_id=schedule.item_id)
        return schedule

    async def execute_scheduled_publish(self, item_id: str) -> ContentItem:
        schedule = self._schedules.get(item_id)
        if schedule is None:
            raise ContentSchedulingError(item_id, "no schedule found")
        if schedule.published:
            raise ContentSchedulingError(item_id, "already published via schedule")
        now = utc_now()
        if now < schedule.publish_at:
            raise ContentSchedulingError(item_id, "publish time not yet reached")
        item = await self.publish_item(item_id)
        self._schedules[item_id] = schedule.__class__(
            id=schedule.id,
            item_id=schedule.item_id,
            publish_at=schedule.publish_at,
            expire_at=schedule.expire_at,
            published=True,
            created_at=schedule.created_at,
        )
        await self._event_bus.publish(
            ContentScheduledPublished(item_id=item_id, schedule_id=schedule.id)
        )
        return item

    async def expire_scheduled(self, item_id: str) -> None:
        schedule = self._schedules.get(item_id)
        if schedule is None:
            raise ContentSchedulingError(item_id, "no schedule found")
        if schedule.expire_at and utc_now() >= schedule.expire_at:
            await self.archive_item(item_id)
            await self._event_bus.publish(
                ContentScheduledExpired(item_id=item_id, schedule_id=schedule.id)
            )

    async def add_localization(
        self,
        item_id: str,
        localization: ContentLocalization,
    ) -> ContentLocalization:
        await self.get_item(item_id)
        self._localizations[item_id].append(localization)
        await self._event_bus.publish(
            ContentLocalizationAdded(item_id=item_id, locale=localization.locale)
        )
        self._log.info("content.localization.added", item_id=item_id, locale=localization.locale)
        return localization

    async def update_localization(
        self,
        item_id: str,
        locale: str,
        body: str,
    ) -> ContentLocalization:
        await self.get_item(item_id)
        locs = self._localizations.get(item_id, [])
        for i, loc in enumerate(locs):
            if loc.locale == locale:
                updated = loc.__class__(
                    id=loc.id,
                    item_id=loc.item_id,
                    locale=loc.locale,
                    title=loc.title,
                    body=body,
                    metadata=loc.metadata,
                    created_at=loc.created_at,
                    updated_at=utc_now(),
                )
                locs[i] = updated
                await self._event_bus.publish(
                    ContentLocalizationUpdated(item_id=item_id, locale=locale)
                )
                self._log.info("content.localization.updated", item_id=item_id, locale=locale)
                return updated
        raise ContentLocalizationError(item_id, f"localization not found for locale {locale!r}")

    async def get_localizations(self, item_id: str) -> list[ContentLocalization]:
        await self.get_item(item_id)
        return list(self._localizations.get(item_id, []))

    async def record_analytics(self, item_id: str, analytics: ContentAnalytics) -> ContentAnalytics:
        self._analytics[item_id].append(analytics)
        await self._event_bus.publish(
            ContentAnalyticsCollected(
                item_id=item_id,
                views=analytics.views,
                unique_visitors=analytics.unique_visitors,
            )
        )
        self._log.info("content.analytics.recorded", item_id=item_id)
        return analytics

    async def get_analytics(self, item_id: str) -> list[ContentAnalytics]:
        await self.get_item(item_id)
        return list(self._analytics.get(item_id, []))

    async def set_permission(
        self,
        item_id: str,
        permission: ContentPermission,
    ) -> ContentPermission:
        await self.get_item(item_id)
        existing = self._permissions.get(item_id, [])
        self._permissions[item_id] = [p for p in existing if p.principal != permission.principal]
        self._permissions[item_id].append(permission)
        await self._event_bus.publish(
            ContentPermissionsUpdated(
                item_id=item_id,
                principal=permission.principal,
                permission=permission.permission,
            )
        )
        self._log.info("content.permission.set", item_id=item_id, principal=permission.principal)
        return permission

    async def check_permission(self, item_id: str, principal: str, permission: str) -> bool:
        for p in self._permissions.get(item_id, []):
            if p.principal == principal and p.permission == permission:
                return True
        return False

    async def create_subscription(
        self,
        item_id: str,
        subscription: ContentSubscription,
    ) -> ContentSubscription:
        await self.get_item(item_id)
        self._subscriptions[item_id].append(subscription)
        await self._event_bus.publish(
            ContentSubscriptionCreated(item_id=item_id, subscriber=subscription.subscriber)
        )
        self._log.info("content.subscription.created", item_id=item_id)
        return subscription

    async def remove_subscription(self, item_id: str, subscriber: str) -> None:
        await self.get_item(item_id)
        prev = self._subscriptions.get(item_id, [])
        self._subscriptions[item_id] = [s for s in prev if s.subscriber != subscriber]
        await self._event_bus.publish(
            ContentSubscriptionRemoved(item_id=item_id, subscriber=subscriber)
        )
        self._log.info("content.subscription.removed", item_id=item_id)

    async def create_collection(self, collection: ContentCollection) -> ContentCollection:
        self._collections[collection.id] = collection
        self._log.info("content.collection.created", collection_id=collection.id)
        return collection

    async def get_collection(self, collection_id: str) -> ContentCollection:
        collection = self._collections.get(collection_id)
        if collection is None:
            raise ContentNotFoundError(collection_id)
        return collection

    async def list_collections(self) -> list[ContentCollection]:
        return list(self._collections.values())

    async def add_item_to_collection(self, collection_id: str, item_id: str) -> ContentCollection:
        collection = await self.get_collection(collection_id)
        await self.get_item(item_id)
        if item_id not in collection.items:
            new_items = [*collection.items, item_id]
            updated = collection.__class__(
                id=collection.id,
                name=collection.name,
                description=collection.description,
                items=tuple(new_items),
                tags=collection.tags,
                created_at=collection.created_at,
                updated_at=utc_now(),
            )
            self._collections[collection_id] = updated
            return updated
        return collection


__all__ = ["ContentManagementService"]
