"""Tests for CacheInvalidator service."""

from __future__ import annotations

import pytest

from eaip.cacheinv.exceptions import InvalidationError, TagNotFoundError
from eaip.cacheinv.invalidator import CacheInvalidator
from eaip.cacheinv.models import (
    CacheTag,
    InvalidationRequest,
    InvalidationResult,
    InvalidatorConfig,
)


class TestCacheInvalidator:
    @pytest.fixture
    def invalidator(self) -> CacheInvalidator:
        return CacheInvalidator()

    @pytest.fixture
    def sample_tag(self) -> CacheTag:
        return CacheTag(id="tag1", pattern="users:*", ttl_seconds=300)

    class TestRegisterTag:
        async def test_register_tag(
            self, invalidator: CacheInvalidator, sample_tag: CacheTag
        ) -> None:
            result = await invalidator.register_tag(sample_tag)
            assert result.id == "tag1"
            assert result.pattern == "users:*"

        async def test_list_tags(self, invalidator: CacheInvalidator, sample_tag: CacheTag) -> None:
            await invalidator.register_tag(sample_tag)
            tags = await invalidator.list_tags()
            assert len(tags) == 1

    class TestGetTag:
        async def test_get_tag(self, invalidator: CacheInvalidator, sample_tag: CacheTag) -> None:
            await invalidator.register_tag(sample_tag)
            tag = await invalidator.get_tag("tag1")
            assert tag.ttl_seconds == 300

        async def test_get_tag_not_found(self, invalidator: CacheInvalidator) -> None:
            with pytest.raises(TagNotFoundError):
                await invalidator.get_tag("nonexistent")

    class TestInvalidate:
        async def test_invalidate_by_tags(
            self, invalidator: CacheInvalidator, sample_tag: CacheTag
        ) -> None:
            await invalidator.register_tag(sample_tag)
            request = InvalidationRequest(id="req1", tags=("tag1",), reason="update")
            result = await invalidator.invalidate(request)
            assert result.request_id == "req1"
            assert result.invalidated_count >= 1

        async def test_invalidate_by_pattern(
            self, invalidator: CacheInvalidator, sample_tag: CacheTag
        ) -> None:
            await invalidator.register_tag(sample_tag)
            request = InvalidationRequest(id="req1", pattern="users:*", reason="bulk")
            result = await invalidator.invalidate(request)
            assert result.request_id == "req1"

        async def test_invalidate_empty(self, invalidator: CacheInvalidator) -> None:
            request = InvalidationRequest(id="req1", tags=(), reason="none")
            result = await invalidator.invalidate(request)
            assert result.invalidated_count == 0

    class TestPurgeTag:
        async def test_purge_tag(self, invalidator: CacheInvalidator, sample_tag: CacheTag) -> None:
            await invalidator.register_tag(sample_tag)
            event = await invalidator.purge_tag("tag1")
            assert event.tag == "tag1"
            assert event.entries_removed > 0

        async def test_purge_tag_not_found(self, invalidator: CacheInvalidator) -> None:
            with pytest.raises(TagNotFoundError):
                await invalidator.purge_tag("nonexistent")

    class TestBulkInvalidate:
        async def test_bulk_invalidate(
            self, invalidator: CacheInvalidator, sample_tag: CacheTag
        ) -> None:
            await invalidator.register_tag(sample_tag)
            requests = [
                InvalidationRequest(id="req1", tags=("tag1",), reason="update"),
                InvalidationRequest(id="req2", tags=("tag1",), reason="update"),
            ]
            result = await invalidator.bulk_invalidate(requests)
            assert result.total_invalidated >= 2

    class TestGetInvalidationRequest:
        async def test_get_request(self, invalidator: CacheInvalidator) -> None:
            request = InvalidationRequest(id="req1", tags=("tag1",), reason="test")
            await invalidator.invalidate(request)
            result = await invalidator.get_invalidation_request("req1")
            assert result.reason == "test"

        async def test_get_request_not_found(self, invalidator: CacheInvalidator) -> None:
            with pytest.raises(TagNotFoundError):
                await invalidator.get_invalidation_request("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            i = CacheInvalidator()
            assert i.config.batch_size == 100
            assert i.config.max_tags_per_request == 50

        def test_custom_config(self) -> None:
            config = InvalidatorConfig(batch_size=50, concurrency_limit=5)
            i = CacheInvalidator(config=config)
            assert i.config.batch_size == 50
            assert i.config.concurrency_limit == 5
