"""Tests for EventRetentionManager."""

from __future__ import annotations

import pytest

from eaip.eventret.exceptions import PolicyNotFoundError
from eaip.eventret.manager import EventRetentionManager
from eaip.eventret.models import (
    EventRetentionConfig,
    RetentionAction,
    RetentionJobStatus,
    RetentionPolicy,
)


class TestEventRetentionManager:
    @pytest.fixture
    def manager(self) -> EventRetentionManager:
        return EventRetentionManager()

    @pytest.fixture
    def sample_policy(self) -> RetentionPolicy:
        return RetentionPolicy(
            id="p1", name="cleanup-90d", max_age_days=90, action=RetentionAction.DELETE
        )

    class TestCreatePolicy:
        async def test_creates_policy(
            self, manager: EventRetentionManager, sample_policy: RetentionPolicy
        ) -> None:
            result = await manager.create_policy(sample_policy)
            assert result.id == "p1"
            assert result.name == "cleanup-90d"

        async def test_stores_policy(
            self, manager: EventRetentionManager, sample_policy: RetentionPolicy
        ) -> None:
            await manager.create_policy(sample_policy)
            stored = await manager.get_policy("p1")
            assert stored.max_age_days == 90

    class TestGetPolicy:
        async def test_returns_policy(
            self, manager: EventRetentionManager, sample_policy: RetentionPolicy
        ) -> None:
            await manager.create_policy(sample_policy)
            result = await manager.get_policy("p1")
            assert result.action == RetentionAction.DELETE

        async def test_raises_on_missing(self, manager: EventRetentionManager) -> None:
            with pytest.raises(PolicyNotFoundError):
                await manager.get_policy("nonexistent")

    class TestUpdatePolicy:
        async def test_updates_policy(
            self, manager: EventRetentionManager, sample_policy: RetentionPolicy
        ) -> None:
            await manager.create_policy(sample_policy)
            result = await manager.update_policy("p1", max_age_days=60)
            assert result.max_age_days == 60

        async def test_raises_on_missing(self, manager: EventRetentionManager) -> None:
            with pytest.raises(PolicyNotFoundError):
                await manager.update_policy("nonexistent", max_age_days=30)

    class TestDeletePolicy:
        async def test_deletes_policy(
            self, manager: EventRetentionManager, sample_policy: RetentionPolicy
        ) -> None:
            await manager.create_policy(sample_policy)
            await manager.delete_policy("p1")
            assert await manager.list_policies() == []

        async def test_raises_on_missing(self, manager: EventRetentionManager) -> None:
            with pytest.raises(PolicyNotFoundError):
                await manager.delete_policy("nonexistent")

    class TestApplyPolicy:
        async def test_applies_policy(
            self, manager: EventRetentionManager, sample_policy: RetentionPolicy
        ) -> None:
            await manager.create_policy(sample_policy)
            job = await manager.apply_policy("p1", "j1")
            assert job.status in (RetentionJobStatus.COMPLETED, RetentionJobStatus.FAILED)

        async def test_raises_on_missing_policy(self, manager: EventRetentionManager) -> None:
            with pytest.raises(PolicyNotFoundError):
                await manager.apply_policy("nonexistent", "j1")

        async def test_raises_on_disabled_policy(self, manager: EventRetentionManager) -> None:
            policy = RetentionPolicy(
                id="p2", name="disabled", action=RetentionAction.DELETE, enabled=False
            )
            await manager.create_policy(policy)
            with pytest.raises(PolicyNotFoundError):
                await manager.apply_policy("p2", "j2")

    class TestListPolicies:
        async def test_filters_enabled(
            self, manager: EventRetentionManager, sample_policy: RetentionPolicy
        ) -> None:
            await manager.create_policy(sample_policy)
            p2 = RetentionPolicy(
                id="p2", name="disabled", action=RetentionAction.ARCHIVE, enabled=False
            )
            await manager.create_policy(p2)
            policies = await manager.list_policies(enabled_only=True)
            assert len(policies) == 1

    class TestGetStatistics:
        async def test_returns_stats(
            self, manager: EventRetentionManager, sample_policy: RetentionPolicy
        ) -> None:
            await manager.create_policy(sample_policy)
            stats = await manager.get_statistics()
            assert stats["total_policies"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = EventRetentionManager()
            assert svc.config.default_max_age_days == 90

        def test_custom_config(self) -> None:
            cfg = EventRetentionConfig(default_max_age_days=30)
            svc = EventRetentionManager(config=cfg)
            assert svc.config.default_max_age_days == 30
