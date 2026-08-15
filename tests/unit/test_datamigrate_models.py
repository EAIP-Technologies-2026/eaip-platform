from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.datamigrate.models import (
    BatchStatus,
    DataTransform,
    Migration,
    MigrationBatch,
    MigrationConfig,
    MigrationStatus,
    MigrationStep,
    MigrationType,
    StepDirection,
    StepStatus,
)


class TestMigrationModels:
    def test_migration_defaults(self) -> None:
        m = Migration(
            id="m1", name="test", version="1.0", description="desc", type=MigrationType.DATA
        )
        assert m.status == MigrationStatus.PENDING
        assert m.duration_ms == 0.0
        assert m.error is None

    def test_migration_frozen(self) -> None:
        m = Migration(
            id="m1", name="test", version="1.0", description="desc", type=MigrationType.DATA
        )
        with pytest.raises((TypeError, ValidationError)):
            m.name = "changed"  # type: ignore[misc]

    def test_migration_step_defaults(self) -> None:
        s = MigrationStep(
            id="s1", migration_id="m1", order=1, description="step 1", type=StepDirection.UP
        )
        assert s.status == StepStatus.PENDING
        assert s.duration_ms == 0.0

    def test_migration_batch_defaults(self) -> None:
        b = MigrationBatch(id="b1", name="batch 1")
        assert b.status == BatchStatus.PENDING
        assert b.migrations == ()

    def test_data_transform_defaults(self) -> None:
        t = DataTransform(id="t1", name="transform", source_type="csv", target_type="json")
        assert t.enabled is True
        assert t.mapping_rules == {}

    def test_migration_config_defaults(self) -> None:
        c = MigrationConfig()
        assert c.enable_auto_migrate is True
        assert c.backup_before_migrate is True
        assert c.max_retries == 3
        assert c.concurrent_migrations == 1

    def test_migration_type_enum(self) -> None:
        assert MigrationType.SCHEMA.value == "schema"
        assert MigrationType.DATA.value == "data"

    def test_migration_status_enum(self) -> None:
        assert MigrationStatus.ROLLED_BACK.value == "rolled_back"


class TestMigrationEngine:
    @pytest.mark.asyncio
    async def test_register_and_run_migration(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine

        engine = MigrationEngine()
        migration = engine.register_migration(
            migration_id="m1",
            name="test migration",
            version="1.0",
            description="test",
        )
        assert migration.id == "m1"
        assert migration.status == MigrationStatus.PENDING

        result = await engine.run_migration("m1")
        assert result.status == MigrationStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_run_nonexistent_migration(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine
        from eaip.datamigrate.exceptions import MigrationNotFoundError

        engine = MigrationEngine()
        with pytest.raises(MigrationNotFoundError):
            await engine.run_migration("nonexistent")

    @pytest.mark.asyncio
    async def test_get_migration(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine

        engine = MigrationEngine()
        engine.register_migration(migration_id="m1", name="test", version="1.0", description="test")
        result = await engine.get_migration("m1")
        assert result.id == "m1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_migration(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine
        from eaip.datamigrate.exceptions import MigrationNotFoundError

        engine = MigrationEngine()
        with pytest.raises(MigrationNotFoundError):
            await engine.get_migration("nonexistent")

    @pytest.mark.asyncio
    async def test_list_migrations(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine

        engine = MigrationEngine()
        engine.register_migration(migration_id="m1", name="a", version="1.0", description="test")
        engine.register_migration(migration_id="m2", name="b", version="1.0", description="test")
        all_m = await engine.list_migrations()
        assert len(all_m) == 2

    @pytest.mark.asyncio
    async def test_verify_migration(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine

        engine = MigrationEngine()
        engine.register_migration(migration_id="m1", name="test", version="1.0", description="test")
        await engine.run_migration("m1")
        valid = await engine.verify_migration("m1")
        assert valid is True

    @pytest.mark.asyncio
    async def test_migration_with_handler(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine

        called = False

        async def handler(migration: object) -> None:
            nonlocal called
            called = True

        engine = MigrationEngine()
        engine.register_migration(
            migration_id="m1", name="test", version="1.0", description="test", handler=handler
        )
        await engine.run_migration("m1")
        assert called

    @pytest.mark.asyncio
    async def test_migration_failure(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine
        from eaip.datamigrate.exceptions import MigrationFailedError

        async def failing_handler(migration: object) -> None:
            msg = "handler error"
            raise ValueError(msg)

        engine = MigrationEngine()
        engine.register_migration(
            migration_id="m1",
            name="test",
            version="1.0",
            description="test",
            handler=failing_handler,
        )
        with pytest.raises(MigrationFailedError):
            await engine.run_migration("m1")

        migration = await engine.get_migration("m1")
        assert migration.status == MigrationStatus.FAILED

    @pytest.mark.asyncio
    async def test_rollback_migration(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine
        from eaip.datamigrate.models import MigrationStep, StepDirection

        engine = MigrationEngine()
        rollback_handler_called = False

        async def rollback_handler(step: object) -> None:
            nonlocal rollback_handler_called
            rollback_handler_called = True

        step = MigrationStep(
            id="s1",
            migration_id="m1",
            order=1,
            description="rollback step",
            type=StepDirection.ROLLBACK,
        )
        engine.register_migration(
            migration_id="m1",
            name="test",
            version="1.0",
            description="test",
            steps=[step],
        )
        engine._handlers["m1:step:s1"] = rollback_handler
        await engine.run_migration("m1")
        result = await engine.rollback_migration("m1")
        assert result.status == MigrationStatus.ROLLED_BACK
        assert rollback_handler_called

    @pytest.mark.asyncio
    async def test_rollback_uncompleted_migration(self) -> None:
        from eaip.datamigrate.engine import MigrationEngine
        from eaip.datamigrate.exceptions import RollbackFailedError

        engine = MigrationEngine()
        engine.register_migration(migration_id="m1", name="test", version="1.0", description="test")
        with pytest.raises(RollbackFailedError):
            await engine.rollback_migration("m1")
