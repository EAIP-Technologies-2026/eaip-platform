from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m018")


async def up(conn) -> None:
    log.info("Running migration m018_m1_memory_knowledge: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS org_memory (
                memory_id       VARCHAR NOT NULL,
                organization_id VARCHAR NOT NULL,
                memory_type     VARCHAR NOT NULL DEFAULT 'enterprise_fact',
                subject         VARCHAR NOT NULL DEFAULT '',
                content         TEXT NOT NULL DEFAULT '',
                confidence      FLOAT NOT NULL DEFAULT 0.8,
                status          VARCHAR NOT NULL DEFAULT 'active',
                valid_from      TIMESTAMPTZ,
                valid_until     TIMESTAMPTZ,
                supersedes      VARCHAR,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (memory_id, organization_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orgmem_org ON org_memory(organization_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orgmem_type ON org_memory(memory_type)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orgmem_subject ON org_memory(subject)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_orgmem_valid ON org_memory(valid_from, valid_until)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS temporal_knowledge (
                record_id       VARCHAR NOT NULL,
                organization_id VARCHAR NOT NULL,
                subject         VARCHAR NOT NULL DEFAULT '',
                content         TEXT NOT NULL DEFAULT '',
                valid_from      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                valid_until     TIMESTAMPTZ,
                status          VARCHAR NOT NULL DEFAULT 'active',
                version         INT NOT NULL DEFAULT 1,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (record_id, organization_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_tk_org ON temporal_knowledge(organization_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_tk_subject ON temporal_knowledge(subject)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_tk_valid ON temporal_knowledge(valid_from, valid_until)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS decision_memory (
                decision_id     VARCHAR NOT NULL,
                organization_id VARCHAR NOT NULL,
                title           VARCHAR NOT NULL DEFAULT '',
                status          VARCHAR NOT NULL DEFAULT 'draft',
                owner           VARCHAR NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (decision_id, organization_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_decision_org ON decision_memory(organization_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m018 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("decision_memory", "temporal_knowledge", "org_memory"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m018 down fallback", error=repr(exc))


migration = Migration(id="m018_m1_memory_knowledge", description="M1: org memory, temporal knowledge, decision memory", up=up, down=down)
