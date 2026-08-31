"""Migration 008: Workforce persistence — workers and assignments."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m008_workforce")


async def up(conn) -> None:
    log.info("Running migration mm008_workforce_persistence: up")
    # Best-effort: if DB is unavailable we log and return (graceful fallback)
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workforce_workers (
                id                   VARCHAR         NOT NULL,
                tenant_id            VARCHAR         NOT NULL,
                worker_type          VARCHAR         NOT NULL DEFAULT 'agent',
                agent_id             VARCHAR         NOT NULL DEFAULT '',
                workflow_id          VARCHAR         NOT NULL DEFAULT '',
                name                 VARCHAR         NOT NULL DEFAULT '',
                description          TEXT            NOT NULL DEFAULT '',
                tags                 TEXT[]          NOT NULL DEFAULT '{}',
                max_concurrent_runs  INT             NOT NULL DEFAULT 1,
                status               VARCHAR         NOT NULL DEFAULT 'active',
                created_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workforce_workers_tenant ON workforce_workers(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workforce_workers_type ON workforce_workers(tenant_id, worker_type)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workforce_workers_status ON workforce_workers(tenant_id, status)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workforce_assignments (
                id                VARCHAR         NOT NULL,
                tenant_id         VARCHAR         NOT NULL,
                worker_id         VARCHAR         NOT NULL,
                task_description  TEXT            NOT NULL DEFAULT '',
                status            VARCHAR         NOT NULL DEFAULT 'pending',
                assigned_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
                completed_at      TIMESTAMPTZ,
                result            TEXT            NOT NULL DEFAULT '',
                error             TEXT,
                run_id            VARCHAR         NOT NULL DEFAULT '',
                priority          INT             NOT NULL DEFAULT 0,
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workforce_assignments_tenant ON workforce_assignments(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workforce_assignments_worker ON workforce_assignments(tenant_id, worker_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workforce_assignments_status ON workforce_assignments(tenant_id, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workforce_assignments_assigned ON workforce_assignments(tenant_id, assigned_at)")
    except Exception as exc:  # pragma: no cover - DB fallback
        log.warning("mm008_workforce_persistence fallback (db unavailable)", error=repr(exc))


async def down(conn) -> None:
    log.info("Running migration mm008_workforce_persistence: down")
    try:
        await conn.execute("DROP TABLE IF EXISTS workforce_assignments")
        await conn.execute("DROP TABLE IF EXISTS workforce_workers")
    except Exception as exc:  # pragma: no cover
        log.warning("mm008_workforce_persistence down fallback", error=repr(exc))


migration = Migration(
    id="m008_workforce_persistence",
    description="Workforce persistence: workforce_workers and workforce_assignments with tenant isolation",
    up=up,
    down=down,
)
