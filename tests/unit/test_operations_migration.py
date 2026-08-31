"""Tests for :mod:`eaip.operations.migration`."""

from __future__ import annotations

import pytest

from eaip.operations.exceptions import MigrationError, MigrationValidationError
from eaip.operations.migration import MigrationService
from eaip.operations.models import MigrationPlan, MigrationStep


@pytest.fixture
def service() -> MigrationService:
    return MigrationService()


@pytest.fixture
def draft_plan() -> MigrationPlan:
    step = MigrationStep(id="s1", description="Migrate data", type="data")
    return MigrationPlan(
        id="mp-1",
        name="v2 upgrade",
        source_version="1.0",
        target_version="2.0",
        steps=(step,),
        status="draft",
    )


class TestMigrationService:
    async def test_create_plan(self, service: MigrationService, draft_plan: MigrationPlan) -> None:
        result = await service.create_migration_plan(draft_plan)
        assert result.id == "mp-1"
        assert result.status == "draft"

    async def test_get_migration(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        result = await service.get_migration("mp-1")
        assert result is not None
        assert result.name == "v2 upgrade"

    async def test_get_migration_not_found(self, service: MigrationService) -> None:
        result = await service.get_migration("does-not-exist")
        assert result is None

    async def test_list_migrations(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        plans = await service.list_migrations()
        assert len(plans) == 1

    async def test_list_migrations_empty(self, service: MigrationService) -> None:
        plans = await service.list_migrations()
        assert plans == []

    async def test_validate_plan(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        validated = await service.validate_plan("mp-1")
        assert validated.status == "validated"

    async def test_validate_plan_not_found(self, service: MigrationService) -> None:
        with pytest.raises(MigrationValidationError):
            await service.validate_plan("does-not-exist")

    async def test_validate_plan_wrong_status(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        await service.validate_plan("mp-1")
        with pytest.raises(MigrationValidationError, match="expected 'draft'"):
            await service.validate_plan("mp-1")

    async def test_validate_plan_no_steps(self, service: MigrationService) -> None:
        plan = MigrationPlan(
            id="mp-empty",
            name="empty",
            source_version="1.0",
            target_version="2.0",
            steps=(),
            status="draft",
        )
        await service.create_migration_plan(plan)
        with pytest.raises(MigrationValidationError, match="no migration steps"):
            await service.validate_plan("mp-empty")

    async def test_execute_migration(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        await service.validate_plan("mp-1")
        executed = await service.execute_migration("mp-1")
        assert executed.status == "completed"
        assert executed.completed_at is not None
        assert executed.steps[0].status == "completed"

    async def test_execute_migration_not_found(self, service: MigrationService) -> None:
        with pytest.raises(MigrationError):
            await service.execute_migration("does-not-exist")

    async def test_execute_migration_wrong_status(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        with pytest.raises(MigrationError, match="expected 'validated'"):
            await service.execute_migration("mp-1")

    async def test_rollback_migration(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        await service.validate_plan("mp-1")
        await service.execute_migration("mp-1")
        rolled = await service.rollback_migration("mp-1")
        assert rolled.status == "rolled_back"

    async def test_rollback_migration_not_found(self, service: MigrationService) -> None:
        with pytest.raises(MigrationError):
            await service.rollback_migration("does-not-exist")

    async def test_rollback_migration_wrong_status(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        with pytest.raises(MigrationError, match="expected 'completed' or 'failed'"):
            await service.rollback_migration("mp-1")

    async def test_full_lifecycle(
        self, service: MigrationService, draft_plan: MigrationPlan
    ) -> None:
        await service.create_migration_plan(draft_plan)
        assert (await service.get_migration("mp-1")).status == "draft"
        await service.validate_plan("mp-1")
        assert (await service.get_migration("mp-1")).status == "validated"
        await service.execute_migration("mp-1")
        assert (await service.get_migration("mp-1")).status == "completed"
        await service.rollback_migration("mp-1")
        assert (await service.get_migration("mp-1")).status == "rolled_back"
