"""Migration 009: Simulation persistence — durable simulation events."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.mm009_simulation")


async def up(conn) -> None:
    log.info("Running migration mm009_simulation: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS simulation_events (
                id              VARCHAR         PRIMARY KEY,
                tenant_id       VARCHAR         NOT NULL,
                enterprise      VARCHAR         NOT NULL,
                event_type      VARCHAR         NOT NULL,
                payload         JSONB           NOT NULL DEFAULT '{}'::jsonb,
                created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_simulation_events_tenant ON simulation_events(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_simulation_events_enterprise ON simulation_events(tenant_id, enterprise)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_simulation_events_type ON simulation_events(event_type)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_simulation_events_created ON simulation_events(created_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_simulation_events_tenant_created ON simulation_events(tenant_id, created_at)")
    except Exception as exc:  # pragma: no cover - DB fallback
        log.warning("mm009_simulation fallback (db unavailable)", error=repr(exc))


async def down(conn) -> None:
    log.info("Running migration mm009_simulation: down")
    try:
        await conn.execute("DROP TABLE IF EXISTS simulation_events")
    except Exception as exc:  # pragma: no cover
        log.warning("mm009_simulation down fallback", error=repr(exc))


migration = Migration(
    id="m009_simulation",
    description="Simulation persistence: simulation_events table with indexes",
    up=up,
    down=down,
)
