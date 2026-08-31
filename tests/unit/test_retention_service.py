"""Tests for RetentionService."""

from __future__ import annotations

import pytest

from eaip.retention.exceptions import PolicyNotFoundError, PurgeExecutionError
from eaip.retention.models import PurgeStatus, RetentionConfig, RetentionPolicy
from eaip.retention.service import RetentionService


class TestRetentionService:
    @pytest.fixture
    def service(self) -> RetentionService:
        return RetentionService()

    @pytest.fixture
    def sample_policy(self) -> RetentionPolicy:
        return RetentionPolicy(id="p1", name="Clean logs", data_type="logs", retention_days=30)

    class TestCreatePolicy:
        async def test_create(
            self, service: RetentionService, sample_policy: RetentionPolicy
        ) -> None:
            result = await service.create_policy(sample_policy)
            assert result.id == "p1"
            assert result.name == "Clean logs"

        async def test_list(
            self, service: RetentionService, sample_policy: RetentionPolicy
        ) -> None:
            await service.create_policy(sample_policy)
            policies = await service.list_policies()
            assert len(policies) == 1

    class TestGetPolicy:
        async def test_get(self, service: RetentionService, sample_policy: RetentionPolicy) -> None:
            await service.create_policy(sample_policy)
            policy = await service.get_policy("p1")
            assert policy.name == "Clean logs"

        async def test_get_not_found(self, service: RetentionService) -> None:
            with pytest.raises(PolicyNotFoundError):
                await service.get_policy("nonexistent")

    class TestUpdatePolicy:
        async def test_update(
            self, service: RetentionService, sample_policy: RetentionPolicy
        ) -> None:
            await service.create_policy(sample_policy)
            updated = await service.update_policy("p1", name="New Name")
            assert updated.name == "New Name"

        async def test_update_not_found(self, service: RetentionService) -> None:
            with pytest.raises(PolicyNotFoundError):
                await service.update_policy("nonexistent", name="X")

    class TestDeletePolicy:
        async def test_delete(
            self, service: RetentionService, sample_policy: RetentionPolicy
        ) -> None:
            await service.create_policy(sample_policy)
            await service.delete_policy("p1")
            with pytest.raises(PolicyNotFoundError):
                await service.get_policy("p1")

        async def test_delete_not_found(self, service: RetentionService) -> None:
            with pytest.raises(PolicyNotFoundError):
                await service.delete_policy("nonexistent")

    class TestExecutePurge:
        async def test_execute_purge(
            self, service: RetentionService, sample_policy: RetentionPolicy
        ) -> None:
            await service.create_policy(sample_policy)
            job = await service.execute_purge("p1")
            assert job.status == PurgeStatus.COMPLETED
            assert job.policy_id == "p1"
            assert job.total_items > 0
            assert job.purged_items > 0

        async def test_execute_disabled_policy(self, service: RetentionService) -> None:
            policy = RetentionPolicy(id="p1", name="Disabled", enabled=False)
            await service.create_policy(policy)
            with pytest.raises(PurgeExecutionError):
                await service.execute_purge("p1")

        async def test_execute_not_found(self, service: RetentionService) -> None:
            with pytest.raises(PolicyNotFoundError):
                await service.execute_purge("nonexistent")

    class TestSchedulePurge:
        async def test_schedule(
            self, service: RetentionService, sample_policy: RetentionPolicy
        ) -> None:
            await service.create_policy(sample_policy)
            job = await service.schedule_purge("p1")
            assert job.status == PurgeStatus.COMPLETED

    class TestGetPurgeHistory:
        async def test_get_history(
            self, service: RetentionService, sample_policy: RetentionPolicy
        ) -> None:
            await service.create_policy(sample_policy)
            await service.execute_purge("p1")
            history = await service.get_purge_history("p1")
            assert len(history) == 1
            assert history[0].policy_id == "p1"

        async def test_get_all_history(
            self, service: RetentionService, sample_policy: RetentionPolicy
        ) -> None:
            await service.create_policy(sample_policy)
            await service.execute_purge("p1")
            all_jobs = await service.get_purge_history()
            assert len(all_jobs) == 1

    class TestConfig:
        def test_default_config(self) -> None:
            s = RetentionService()
            assert s.config.max_purge_batch_size == 1000
            assert s.config.schedule_interval_minutes == 1440

        def test_custom_config(self) -> None:
            config = RetentionConfig(max_purge_batch_size=500, schedule_interval_minutes=60)
            s = RetentionService(config=config)
            assert s.config.max_purge_batch_size == 500
            assert s.config.schedule_interval_minutes == 60
