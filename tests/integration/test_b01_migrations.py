"""B01 — migration framework verification against PostgreSQL."""

from __future__ import annotations

import pytest

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.migrations import load_all_migrations


class TestMigrations:
    async def test_migration_ordering(self, db: None) -> None:
        ids = [m.id for m in load_all_migrations()]
        assert ids == sorted(ids)
        assert "003_persistence_foundation" in ids
        assert ids.index("001_initial_schema") < ids.index("003_persistence_foundation")

    async def test_idempotent_rerun(self, db: None) -> None:
        from eaip.infrastructure.db.migrations import MigrationEngine

        engine = MigrationEngine(DatabaseConnection, table_name="_eaip_test_migrations")
        await engine.initialize()
        for migration in load_all_migrations():
            engine.register(migration)
        applied = await engine.run_pending()
        assert applied == 0

    async def test_dead_letters_table_exists(self, db: None) -> None:
        has = await DatabaseConnection.fetchval(
            "SELECT to_regclass('public.dead_letters') IS NOT NULL"
        )
        assert has is True

    async def test_tenant_columns_added(self, db: None) -> None:
        for table in ("runtime_events", "agent_runs", "workflow_runs", "audit_events"):
            rows = await DatabaseConnection.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name=$1 AND column_name='tenant_id'",
                table,
            )
            assert rows, f"{table}.tenant_id missing"

    async def test_migration_tracking(self, db: None) -> None:
        rows = await DatabaseConnection.fetch(
            "SELECT id FROM _eaip_test_migrations ORDER BY id"
        )
        ids = [row["id"] for row in rows]
        assert "003_persistence_foundation" in ids