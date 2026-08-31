from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m013")


async def up(conn) -> None:
    log.info("Running migration m013_swarm_longmissions: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_definitions (
                swarm_id      VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                name          VARCHAR NOT NULL,
                coordinator   VARCHAR NOT NULL DEFAULT '',
                specialists   TEXT[] NOT NULL DEFAULT '{}',
                pattern       VARCHAR NOT NULL DEFAULT 'parallel',
                autonomy_level VARCHAR NOT NULL DEFAULT 'SUGGEST',
                tasks         JSONB NOT NULL DEFAULT '[]'::jsonb,
                status        VARCHAR NOT NULL DEFAULT 'pending',
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
                PRIMARY KEY (swarm_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_swarm_tenant ON swarm_definitions(tenant_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS swarm_executions (
                execution_id  VARCHAR NOT NULL,
                swarm_id      VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                status        VARCHAR NOT NULL DEFAULT 'running',
                task_results  JSONB NOT NULL DEFAULT '[]'::jsonb,
                aggregated_result TEXT NOT NULL DEFAULT '',
                started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                completed_at  TIMESTAMPTZ,
                PRIMARY KEY (execution_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_swarm_exec_tenant ON swarm_executions(tenant_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS long_mission_records (
                mission_id    VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                name          VARCHAR NOT NULL,
                status        VARCHAR NOT NULL DEFAULT 'pending',
                steps         JSONB NOT NULL DEFAULT '[]'::jsonb,
                current_step  INT NOT NULL DEFAULT 0,
                checkpoints   JSONB NOT NULL DEFAULT '[]'::jsonb,
                autonomy_level VARCHAR NOT NULL DEFAULT 'SUGGEST',
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
                PRIMARY KEY (mission_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_long_mission_tenant ON long_mission_records(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m013 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        await conn.execute("DROP TABLE IF EXISTS long_mission_records")
        await conn.execute("DROP TABLE IF EXISTS swarm_executions")
        await conn.execute("DROP TABLE IF EXISTS swarm_definitions")
    except Exception as exc:  # pragma: no cover
        log.warning("m013 down fallback", error=repr(exc))


migration = Migration(id="m013_swarm_longmissions", description="Swarm + long-running missions with checkpoint", up=up, down=down)
