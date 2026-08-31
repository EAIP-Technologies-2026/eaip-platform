"""M10 Migration — enterprise loop, objective loop, strategic corrections."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m024")


async def up(conn) -> None:
    log.info("Running migration m024_m10_loop: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m10_loop_runs (
                run_id          VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                objective       TEXT NOT NULL DEFAULT '',
                current_phase   VARCHAR NOT NULL DEFAULT 'observe',
                status          VARCHAR NOT NULL DEFAULT 'pending',
                autonomy_level  VARCHAR NOT NULL DEFAULT 'L2',
                phases_completed JSONB NOT NULL DEFAULT '[]',
                context         JSONB NOT NULL DEFAULT '{}',
                gap_analysis    JSONB NOT NULL DEFAULT '{}',
                options         JSONB NOT NULL DEFAULT '[]',
                chosen_option   JSONB,
                governance_check JSONB NOT NULL DEFAULT '{}',
                simulation_result JSONB NOT NULL DEFAULT '{}',
                workforce_assignment JSONB NOT NULL DEFAULT '{}',
                workflow_id     VARCHAR NOT NULL DEFAULT '',
                execution_result JSONB NOT NULL DEFAULT '{}',
                kpi_result      JSONB NOT NULL DEFAULT '{}',
                outcome         JSONB NOT NULL DEFAULT '{}',
                learning        JSONB NOT NULL DEFAULT '{}',
                proof_refs      JSONB NOT NULL DEFAULT '[]',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (run_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m10loop_tenant ON m10_loop_runs(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m10loop_status ON m10_loop_runs(status)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m10_objective_runs (
                run_id      VARCHAR NOT NULL,
                tenant_id   VARCHAR NOT NULL,
                objective   TEXT NOT NULL DEFAULT '',
                context     JSONB NOT NULL DEFAULT '{}',
                current_state JSONB NOT NULL DEFAULT '{}',
                gap         JSONB NOT NULL DEFAULT '{}',
                options     JSONB NOT NULL DEFAULT '[]',
                governance  JSONB NOT NULL DEFAULT '{}',
                plan        JSONB NOT NULL DEFAULT '{}',
                kpi         JSONB NOT NULL DEFAULT '{}',
                outcome     JSONB NOT NULL DEFAULT '{}',
                learning    JSONB NOT NULL DEFAULT '{}',
                status      VARCHAR NOT NULL DEFAULT 'pending',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (run_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m10obj_tenant ON m10_objective_runs(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m10_corrections (
                correction_id VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                expected      JSONB NOT NULL DEFAULT '{}',
                actual        JSONB NOT NULL DEFAULT '{}',
                cause         TEXT NOT NULL DEFAULT '',
                alternatives  JSONB NOT NULL DEFAULT '[]',
                recommendation TEXT NOT NULL DEFAULT '',
                governance    JSONB NOT NULL DEFAULT '{}',
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (correction_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m10corr_tenant ON m10_corrections(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m024 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("m10_corrections", "m10_objective_runs", "m10_loop_runs"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m024 down fallback", error=repr(exc))


migration = Migration(id="m024_m10_loop", description="M10: enterprise loop, objective loop, strategic corrections", up=up, down=down)
