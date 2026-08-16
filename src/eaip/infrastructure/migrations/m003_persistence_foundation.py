"""B01 persistence foundation — dead letters and tenant scoping.

Extends the existing production schema (m001) with the pieces required by
BATCH 01 (Persistence & Event Foundation):

- a ``dead_letters`` table for capturing failed event handler invocations,
- an additive ``tenant_id`` column on the event / agent run / workflow run
  tables so persisted domain objects can be tenant-scoped without rebuilding
  the existing schema.

Every statement is additive and idempotent: no data is dropped, altered, or
migrated in place.  Rollback drops only the new table; additive columns are
retained (dropping columns on rollback is intentionally avoided).
"""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration


async def up(conn) -> None:
    # ── Additive tenant scoping (matching the tenants domain model) ──
    await conn.execute("ALTER TABLE runtime_events ADD COLUMN IF NOT EXISTS tenant_id TEXT")
    await conn.execute("ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS tenant_id TEXT")
    await conn.execute("ALTER TABLE workflow_runs ADD COLUMN IF NOT EXISTS tenant_id TEXT")
    await conn.execute("ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS tenant_id TEXT")

    # ── Dead letters — failed event handler captures ─────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS dead_letters (
            id TEXT PRIMARY KEY,
            event_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            tenant_id TEXT,
            payload JSONB NOT NULL DEFAULT '{}',
            handler_name TEXT NOT NULL,
            error_message TEXT NOT NULL DEFAULT '',
            error_traceback TEXT,
            retry_count INT NOT NULL DEFAULT 0,
            max_retries INT NOT NULL DEFAULT 3,
            resolved BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_retry_at TIMESTAMPTZ
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_dead_letters_tenant ON dead_letters(tenant_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_dead_letters_resolved ON dead_letters(resolved) "
        "WHERE resolved = FALSE"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_dead_letters_created ON dead_letters(created_at)"
    )


async def down(conn) -> None:
    await conn.execute("DROP TABLE IF EXISTS dead_letters")


migration = Migration(
    id="003_persistence_foundation",
    description="B01: create dead_letters table and add tenant_id scoping to event/agent/workflow tables",
    up=up,
    down=down,
)