from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m015")


async def up(conn) -> None:
    log.info("Running migration m015_wave1_intelligence: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS intelligence_capabilities (
                capability_id   VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                name            VARCHAR NOT NULL,
                description     TEXT NOT NULL DEFAULT '',
                category        VARCHAR NOT NULL DEFAULT 'agent',
                version         VARCHAR NOT NULL DEFAULT '1.0.0',
                provider        VARCHAR NOT NULL DEFAULT 'eaip',
                runtime         VARCHAR NOT NULL DEFAULT 'local',
                required_permissions TEXT[] NOT NULL DEFAULT '{}',
                health          VARCHAR NOT NULL DEFAULT 'healthy',
                availability    FLOAT NOT NULL DEFAULT 1.0,
                lifecycle_status VARCHAR NOT NULL DEFAULT 'active',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (capability_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_intel_cap_tenant ON intelligence_capabilities(tenant_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS intelligence_executions (
                execution_id    VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                capability_id   VARCHAR NOT NULL,
                status          VARCHAR NOT NULL DEFAULT 'pending',
                result          JSONB NOT NULL DEFAULT '{}'::jsonb,
                started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                completed_at    TIMESTAMPTZ,
                PRIMARY KEY (execution_id, tenant_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS supervision_records (
                record_id       VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                agent_id        VARCHAR NOT NULL,
                mission_id      VARCHAR NOT NULL DEFAULT '',
                progress        FLOAT NOT NULL DEFAULT 0,
                confidence      FLOAT NOT NULL DEFAULT 0,
                strategy        VARCHAR NOT NULL DEFAULT 'direct',
                state           VARCHAR NOT NULL DEFAULT 'running',
                escalation      VARCHAR NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (record_id, tenant_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS decision_records (
                decision_id     VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                title           VARCHAR NOT NULL,
                objective       TEXT NOT NULL DEFAULT '',
                status          VARCHAR NOT NULL DEFAULT 'draft',
                recommendation  VARCHAR NOT NULL DEFAULT '',
                confidence      FLOAT NOT NULL DEFAULT 0.5,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (decision_id, tenant_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS coordination_plans (
                plan_id         VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                objective       TEXT NOT NULL,
                priority        VARCHAR NOT NULL DEFAULT 'operational',
                status          VARCHAR NOT NULL DEFAULT 'draft',
                outcome         TEXT NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (plan_id, tenant_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cognitive_hypotheses (
                hypothesis_id   VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                title           VARCHAR NOT NULL,
                confidence      FLOAT NOT NULL DEFAULT 0.5,
                reasoning_strategy VARCHAR NOT NULL DEFAULT 'direct',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (hypothesis_id, tenant_id)
            )
        """)
    except Exception as exc:  # pragma: no cover
        log.warning("m015 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("cognitive_hypotheses", "coordination_plans", "decision_records", "supervision_records", "intelligence_executions", "intelligence_capabilities"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m015 down fallback", error=repr(exc))


migration = Migration(id="m015_wave1_intelligence", description="Wave 1 intelligence: capabilities, executions, supervision, decisions, coordination, hypotheses", up=up, down=down)
