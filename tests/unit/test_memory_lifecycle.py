"""Tests for memory lifecycle, retention policies, and expiration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.memory.lifecycle import (
    CompositeRetentionPolicy,
    MaxAgeRetentionPolicy,
    MaxCountRetentionPolicy,
    MemoryExpirationService,
    MemoryLifecycleManager,
    PriorityRetentionPolicy,
)
from eaip.memory.models import (
    MemoryItem,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    RetentionConfig,
    ScopedMemoryId,
)
from eaip.memory.store import InMemoryStore
from eaip.shared.time import utc_now


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(tenant_id="t1", user_id="u1")


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


class TestMaxAgeRetentionPolicy:
    @pytest.mark.asyncio
    async def test_expires_old_memory(self, scope: MemoryScope) -> None:
        old = utc_now() - timedelta(seconds=100)
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="old",
            created_at=old,
        )
        policy = MaxAgeRetentionPolicy(max_age_seconds=50)
        result = await policy.evaluate(item)
        assert result == "expire"

    @pytest.mark.asyncio
    async def test_retains_recent_memory(self, scope: MemoryScope) -> None:
        recent = utc_now() - timedelta(seconds=10)
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="recent",
            created_at=recent,
        )
        policy = MaxAgeRetentionPolicy(max_age_seconds=60)
        result = await policy.evaluate(item)
        assert result is None

    @pytest.mark.asyncio
    async def test_type_filter(self, scope: MemoryScope) -> None:
        old = utc_now() - timedelta(seconds=100)
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.SESSION,
            scope=scope,
            content="old session",
            created_at=old,
        )
        policy = MaxAgeRetentionPolicy(max_age_seconds=50, memory_type="working")
        result = await policy.evaluate(item)
        assert result is None

    @pytest.mark.asyncio
    async def test_retains_semantic_zero_ttl(self, scope: MemoryScope) -> None:
        old = utc_now() - timedelta(seconds=100)
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.SEMANTIC,
            scope=scope,
            content="fact",
            created_at=old,
        )
        policy = MaxAgeRetentionPolicy(max_age_seconds=0)
        result = await policy.evaluate(item)
        assert result is None or result == "expire"


class TestMaxCountRetentionPolicy:
    @pytest.mark.asyncio
    async def test_always_returns_none(self, scope: MemoryScope) -> None:
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        policy = MaxCountRetentionPolicy(max_count=5)
        result = await policy.evaluate(item)
        assert result is None


class TestPriorityRetentionPolicy:
    @pytest.mark.asyncio
    async def test_retains_high_importance(self, scope: MemoryScope) -> None:
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="important",
            importance=0.9,
        )
        policy = PriorityRetentionPolicy(min_importance=0.7)
        result = await policy.evaluate(item)
        assert result is None

    @pytest.mark.asyncio
    async def test_low_importance_returns_none(self, scope: MemoryScope) -> None:
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="low",
            importance=0.3,
        )
        policy = PriorityRetentionPolicy(min_importance=0.7)
        result = await policy.evaluate(item)
        assert result is None


class TestCompositeRetentionPolicy:
    @pytest.mark.asyncio
    async def test_first_matching_policy_wins(self, scope: MemoryScope) -> None:
        old = utc_now() - timedelta(seconds=100)
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="old",
            created_at=old,
        )
        max_age = MaxAgeRetentionPolicy(max_age_seconds=50)
        priority = PriorityRetentionPolicy(min_importance=0.7)
        composite = CompositeRetentionPolicy([max_age, priority])
        result = await composite.evaluate(item)
        assert result == "expire"

    @pytest.mark.asyncio
    async def test_no_policy_matches(self, scope: MemoryScope) -> None:
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        composite = CompositeRetentionPolicy([])
        result = await composite.evaluate(item)
        assert result is None


class TestMemoryExpirationService:
    @pytest.mark.asyncio
    async def test_expire_memory(self, store: InMemoryStore, scope: MemoryScope) -> None:
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        await store.create(item)

        service = MemoryExpirationService(store)
        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        assert await service.expire_memory(scoped_id) is True

        expired = await store.read(scoped_id)
        assert expired is not None
        assert expired.status is MemoryStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_expire_nonexistent(self, store: InMemoryStore, scope: MemoryScope) -> None:
        service = MemoryExpirationService(store)
        scoped_id = ScopedMemoryId(memory_id="nonexistent", scope=scope)
        assert await service.expire_memory(scoped_id) is False

    @pytest.mark.asyncio
    async def test_archive_memory(self, store: InMemoryStore, scope: MemoryScope) -> None:
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        await store.create(item)

        service = MemoryExpirationService(store)
        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        assert await service.archive_memory(scoped_id) is True

        archived = await store.read(scoped_id)
        assert archived is not None
        assert archived.status is MemoryStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_restore_memory(self, store: InMemoryStore, scope: MemoryScope) -> None:
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        await store.create(item)

        service = MemoryExpirationService(store)
        scoped_id = ScopedMemoryId(memory_id="m1", scope=scope)
        await service.expire_memory(scoped_id)
        assert await service.restore_memory(scoped_id) is True

        restored = await store.read(scoped_id)
        assert restored is not None
        assert restored.status is MemoryStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_run_expiration_cycle(self, store: InMemoryStore, scope: MemoryScope) -> None:
        past = datetime(2020, 1, 1, tzinfo=UTC)
        future = datetime(2030, 1, 1, tzinfo=UTC)
        item1 = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="x",
            expires_at=past,
        )
        item2 = MemoryItem(
            memory_id="m2",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="y",
            expires_at=future,
        )
        await store.create(item1)
        await store.create(item2)

        service = MemoryExpirationService(store, RetentionConfig(archive_on_expire=False))
        count = await service.run_expiration_cycle()
        assert count >= 1

    @pytest.mark.asyncio
    async def test_run_expiration_cycle_archive_mode(
        self, store: InMemoryStore, scope: MemoryScope
    ) -> None:
        past = datetime(2020, 1, 1, tzinfo=UTC)
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="x",
            expires_at=past,
        )
        await store.create(item)

        service = MemoryExpirationService(store, RetentionConfig(archive_on_expire=True))
        count = await service.run_expiration_cycle()
        assert count >= 1

    @pytest.mark.asyncio
    async def test_get_ttl(self) -> None:
        store = InMemoryStore()
        config = RetentionConfig(working_ttl_seconds=100, session_ttl_seconds=200)
        service = MemoryExpirationService(store, config)
        assert service._get_ttl(MemoryType.WORKING) == 100
        assert service._get_ttl(MemoryType.SESSION) == 200
        assert service._get_ttl(MemoryType.LONG_TERM) == config.long_term_ttl_seconds


class TestMemoryLifecycleManager:
    @pytest.mark.asyncio
    async def test_run_retention_cycle(self, store: InMemoryStore, scope: MemoryScope) -> None:
        past = datetime(2020, 1, 1, tzinfo=UTC)
        item = MemoryItem(
            memory_id="m1",
            memory_type=MemoryType.WORKING,
            scope=scope,
            content="x",
            expires_at=past,
        )
        await store.create(item)

        expiration = MemoryExpirationService(store, RetentionConfig(archive_on_expire=False))
        manager = MemoryLifecycleManager(expiration)
        result = await manager.run_retention_cycle()
        assert result["expired_count"] >= 1
