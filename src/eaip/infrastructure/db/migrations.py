from __future__ import annotations

import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.db.migrations")


@dataclass
class Migration:
    id: str
    description: str
    up: Callable[[Any], Coroutine[Any, Any, None]]
    down: Callable[[Any], Coroutine[Any, Any, None]] | None = None
    dependencies: tuple[str, ...] = field(default_factory=tuple)


class MigrationEngine:
    def __init__(self, db: DatabaseConnection, table_name: str = "_eaip_migrations") -> None:
        self._db = db
        self._table_name = table_name
        self._migrations: dict[str, Migration] = {}
        self._pending: list[str] = []
        self._applied: set[str] = set()

    def register(self, migration: Migration) -> None:
        self._migrations[migration.id] = migration

    async def initialize(self) -> None:
        await self._db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._table_name} (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                duration_ms FLOAT NOT NULL DEFAULT 0
            )
        """)
        rows = await self._db.fetch(f"SELECT id FROM {self._table_name}")
        self._applied = {row["id"] for row in rows}
        log.info("migrations.initialized", applied_count=len(self._applied))

    async def get_pending(self) -> list[Migration]:
        ordered = sorted(
            [m for mid, m in self._migrations.items() if mid not in self._applied],
            key=lambda m: m.id,
        )
        return ordered

    async def run_pending(self) -> int:
        pending = await self.get_pending()
        if not pending:
            log.info("migrations.none_pending")
            return 0
        count = 0
        for migration in pending:
            await self.run(migration.id)
            count += 1
        return count

    async def run(self, migration_id: str) -> None:
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise ValueError(f"Migration {migration_id!r} not found")
        if migration_id in self._applied:
            log.info("migrations.already_applied", id=migration_id)
            return

        log.info("migrations.running", id=migration_id, description=migration.description)
        start = time.monotonic()
        async with self._db.transaction() as conn:
            await migration.up(conn)
            elapsed = (time.monotonic() - start) * 1000
            await conn.execute(
                f"INSERT INTO {self._table_name} (id, description, duration_ms) VALUES ($1, $2, $3)",
                migration_id,
                migration.description,
                elapsed,
            )
        self._applied.add(migration_id)
        log.info("migrations.completed", id=migration_id, duration_ms=round(elapsed, 2))

    async def rollback(self, migration_id: str) -> None:
        migration = self._migrations.get(migration_id)
        if migration is None:
            raise ValueError(f"Migration {migration_id!r} not found")
        if migration.down is None:
            raise ValueError(f"Migration {migration_id!r} has no rollback")
        log.info("migrations.rolling_back", id=migration_id)
        async with self._db.transaction() as conn:
            await migration.down(conn)
            await conn.execute(f"DELETE FROM {self._table_name} WHERE id = $1", migration_id)
        self._applied.discard(migration_id)
        log.info("migrations.rolled_back", id=migration_id)

    @property
    def applied_count(self) -> int:
        return len(self._applied)

    @property
    def pending_count(self) -> int:
        return len([mid for mid in self._migrations if mid not in self._applied])


__all__ = ["Migration", "MigrationEngine"]
