"""Tests for content management."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

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
    ContentType,
    ContentVersion,
    ReviewDecision,
)
from eaip.content_management.service import ContentManagementService


@pytest.fixture
def service() -> ContentManagementService:
    return ContentManagementService()


def make_item(item_id: str = "item-1", **kwargs) -> ContentItem:
    return ContentItem(
        id=item_id,
        name=kwargs.get("name", "Test Item"),
        type=kwargs.get("type", ContentType.ARTICLE),
        body=kwargs.get("body", "body content"),
        author=kwargs.get("author", "author-1"),
    )


class TestContentManagementService:
    async def test_create_item(self, service: ContentManagementService) -> None:
        item = make_item()
        result = await service.create_item(item)
        assert result.id == "item-1"
        assert result.status == ContentStatus.DRAFT

    async def test_create_duplicate_raises(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        with pytest.raises(ContentValidationError):
            await service.create_item(item)

    async def test_get_item(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        result = await service.get_item("item-1")
        assert result.id == "item-1"

    async def test_get_item_not_found(self, service: ContentManagementService) -> None:
        with pytest.raises(ContentNotFoundError):
            await service.get_item("nonexistent")

    async def test_update_item(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        updated = await service.update_item("item-1", body="updated body")
        assert updated.body == "updated body"

    async def test_delete_item(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        await service.delete_item("item-1")
        with pytest.raises(ContentNotFoundError):
            await service.get_item("item-1")

    async def test_list_items(self, service: ContentManagementService) -> None:
        await service.create_item(make_item("item-1"))
        await service.create_item(make_item("item-2"))
        items = await service.list_items()
        assert len(items) == 2

    async def test_list_items_filter_by_status(self, service: ContentManagementService) -> None:
        await service.create_item(make_item("item-1"))
        items = await service.list_items(status=ContentStatus.DRAFT)
        assert len(items) == 1
        items = await service.list_items(status=ContentStatus.PUBLISHED)
        assert len(items) == 0

    async def test_publish_item(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        published = await service.publish_item("item-1")
        assert published.status == ContentStatus.PUBLISHED
        assert published.published_at is not None

    async def test_publish_from_archived_raises(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        await service.archive_item("item-1")
        with pytest.raises(ContentPublishError):
            await service.publish_item("item-1")

    async def test_unpublish_item(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        await service.publish_item("item-1")
        unpublished = await service.unpublish_item("item-1")
        assert unpublished.status == ContentStatus.UNPUBLISHED

    async def test_archive_item(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        archived = await service.archive_item("item-1")
        assert archived.status == ContentStatus.ARCHIVED

    async def test_restore_item(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        await service.archive_item("item-1")
        restored = await service.restore_item("item-1")
        assert restored.status == ContentStatus.DRAFT

    async def test_create_version(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        version = ContentVersion(id="v1", item_id="item-1", version="1.0.0", body="v1 body")
        result = await service.create_version("item-1", version)
        assert result.version == "1.0.0"

    async def test_list_versions(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        v1 = ContentVersion(id="v1", item_id="item-1", version="1.0.0", body="v1")
        v2 = ContentVersion(id="v2", item_id="item-1", version="2.0.0", body="v2")
        await service.create_version("item-1", v1)
        await service.create_version("item-1", v2)
        versions = await service.list_versions("item-1")
        assert len(versions) == 2

    async def test_get_version(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        v1 = ContentVersion(id="v1", item_id="item-1", version="1.0.0", body="v1")
        await service.create_version("item-1", v1)
        result = await service.get_version("item-1", "1.0.0")
        assert result.body == "v1"

    async def test_get_version_not_found(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        with pytest.raises(ContentVersionError):
            await service.get_version("item-1", "nonexistent")

    async def test_review_approve(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        review = ContentReview(
            id="r1",
            item_id="item-1",
            reviewer="reviewer-1",
            decision=ReviewDecision.APPROVED,
        )
        await service.review_item("item-1", review)
        stored = await service.get_item("item-1")
        assert stored.status == ContentStatus.APPROVED

    async def test_review_reject(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        review = ContentReview(
            id="r1",
            item_id="item-1",
            reviewer="reviewer-1",
            decision=ReviewDecision.REJECTED,
            comments="needs work",
        )
        await service.review_item("item-1", review)
        reviews = await service.get_reviews("item-1")
        assert len(reviews) == 1
        assert reviews[0].comments == "needs work"

    async def test_schedule_publish(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        future = utc_now() + timedelta(hours=1)
        schedule = ContentPublishSchedule(id="s1", item_id="item-1", publish_at=future)
        result = await service.schedule_publish(schedule)
        assert result.id == "s1"

    async def test_execute_scheduled_publish(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        past = utc_now() - timedelta(minutes=5)
        schedule = ContentPublishSchedule(id="s1", item_id="item-1", publish_at=past)
        await service.schedule_publish(schedule)
        published = await service.execute_scheduled_publish("item-1")
        assert published.status == ContentStatus.PUBLISHED

    async def test_scheduled_publish_not_yet(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        future = utc_now() + timedelta(hours=1)
        schedule = ContentPublishSchedule(id="s1", item_id="item-1", publish_at=future)
        await service.schedule_publish(schedule)
        with pytest.raises(ContentSchedulingError):
            await service.execute_scheduled_publish("item-1")

    async def test_add_localization(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        loc = ContentLocalization(id="l1", item_id="item-1", locale="fr", body="contenu")
        result = await service.add_localization("item-1", loc)
        assert result.locale == "fr"

    async def test_update_localization(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        loc = ContentLocalization(id="l1", item_id="item-1", locale="fr", body="contenu")
        await service.add_localization("item-1", loc)
        updated = await service.update_localization("item-1", "fr", "nouveau contenu")
        assert updated.body == "nouveau contenu"

    async def test_get_localizations(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        loc = ContentLocalization(id="l1", item_id="item-1", locale="fr", body="contenu")
        await service.add_localization("item-1", loc)
        locs = await service.get_localizations("item-1")
        assert len(locs) == 1

    async def test_record_analytics(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        analytics = ContentAnalytics(id="a1", item_id="item-1", views=100, unique_visitors=50)
        await service.record_analytics("item-1", analytics)
        results = await service.get_analytics("item-1")
        assert len(results) == 1
        assert results[0].views == 100

    async def test_set_and_check_permission(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        perm = ContentPermission(id="p1", item_id="item-1", principal="user-1", permission="read")
        await service.set_permission("item-1", perm)
        assert await service.check_permission("item-1", "user-1", "read") is True
        assert await service.check_permission("item-1", "user-1", "write") is False

    async def test_create_subscription(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        sub = ContentSubscription(id="sub1", item_id="item-1", subscriber="user-1")
        await service.create_subscription("item-1", sub)

    async def test_remove_subscription(self, service: ContentManagementService) -> None:
        item = make_item()
        await service.create_item(item)
        sub = ContentSubscription(id="sub1", item_id="item-1", subscriber="user-1")
        await service.create_subscription("item-1", sub)
        await service.remove_subscription("item-1", "user-1")

    async def test_create_collection(self, service: ContentManagementService) -> None:
        collection = ContentCollection(id="col-1", name="Test Collection")
        result = await service.create_collection(collection)
        assert result.id == "col-1"

    async def test_get_collection(self, service: ContentManagementService) -> None:
        collection = ContentCollection(id="col-1", name="Test Collection")
        await service.create_collection(collection)
        result = await service.get_collection("col-1")
        assert result.name == "Test Collection"

    async def test_list_collections(self, service: ContentManagementService) -> None:
        await service.create_collection(ContentCollection(id="col-1", name="C1"))
        await service.create_collection(ContentCollection(id="col-2", name="C2"))
        cols = await service.list_collections()
        assert len(cols) == 2

    async def test_add_item_to_collection(self, service: ContentManagementService) -> None:
        await service.create_collection(ContentCollection(id="col-1", name="C1"))
        await service.create_item(make_item("item-1"))
        updated = await service.add_item_to_collection("col-1", "item-1")
        assert "item-1" in updated.items


class TestEventTypes:
    def test_content_created_event_type(self) -> None:
        assert ContentCreated.event_type == "eaip.content_management.created"

    def test_content_updated_event_type(self) -> None:
        assert ContentUpdated.event_type == "eaip.content_management.updated"

    def test_content_deleted_event_type(self) -> None:
        assert ContentDeleted.event_type == "eaip.content_management.deleted"

    def test_content_published_event_type(self) -> None:
        assert ContentPublished.event_type == "eaip.content_management.published"

    def test_content_unpublished_event_type(self) -> None:
        assert ContentUnpublished.event_type == "eaip.content_management.unpublished"

    def test_content_archived_event_type(self) -> None:
        assert ContentArchived.event_type == "eaip.content_management.archived"

    def test_content_restored_event_type(self) -> None:
        assert ContentRestored.event_type == "eaip.content_management.restored"

    def test_content_reviewed_event_type(self) -> None:
        assert ContentReviewed.event_type == "eaip.content_management.reviewed"

    def test_content_approved_event_type(self) -> None:
        assert ContentApproved.event_type == "eaip.content_management.approved"

    def test_content_rejected_event_type(self) -> None:
        assert ContentRejected.event_type == "eaip.content_management.rejected"

    def test_content_version_created_event_type(self) -> None:
        assert ContentVersionCreated.event_type == "eaip.content_management.version.created"

    def test_content_scheduled_event_type(self) -> None:
        assert ContentScheduled.event_type == "eaip.content_management.scheduled"

    def test_content_scheduled_published_event_type(self) -> None:
        assert ContentScheduledPublished.event_type == "eaip.content_management.scheduled.published"

    def test_content_scheduled_expired_event_type(self) -> None:
        assert ContentScheduledExpired.event_type == "eaip.content_management.scheduled.expired"

    def test_content_localization_added_event_type(self) -> None:
        assert ContentLocalizationAdded.event_type == "eaip.content_management.localization.added"

    def test_content_localization_updated_event_type(self) -> None:
        expected = "eaip.content_management.localization.updated"
        assert ContentLocalizationUpdated.event_type == expected

    def test_content_analytics_collected_event_type(self) -> None:
        expected = "eaip.content_management.analytics.collected"
        assert ContentAnalyticsCollected.event_type == expected

    def test_content_subscription_created_event_type(self) -> None:
        expected = "eaip.content_management.subscription.created"
        assert ContentSubscriptionCreated.event_type == expected

    def test_content_subscription_removed_event_type(self) -> None:
        expected = "eaip.content_management.subscription.removed"
        assert ContentSubscriptionRemoved.event_type == expected

    def test_content_permissions_updated_event_type(self) -> None:
        expected = "eaip.content_management.permissions.updated"
        assert ContentPermissionsUpdated.event_type == expected


def utc_now() -> datetime:
    return datetime.now(UTC)
