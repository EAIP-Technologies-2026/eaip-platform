from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m014")


async def up(conn) -> None:
    log.info("Running migration m014_enterprise_scale: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS runtime_registry (
                runtime_id  VARCHAR NOT NULL PRIMARY KEY,
                kind        VARCHAR NOT NULL DEFAULT 'local_runtime',
                name        VARCHAR NOT NULL,
                capabilities TEXT[] NOT NULL DEFAULT '{}',
                status      VARCHAR NOT NULL DEFAULT 'healthy',
                tenant_id   VARCHAR NOT NULL DEFAULT 'default',
                metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_chain_records (
                record_id     VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                actor         VARCHAR NOT NULL,
                action        VARCHAR NOT NULL,
                previous_hash VARCHAR NOT NULL DEFAULT '',
                record_hash   VARCHAR NOT NULL,
                timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
                PRIMARY KEY (record_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_chain_tenant ON audit_chain_records(tenant_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS federated_orgs (
                org_id        VARCHAR NOT NULL PRIMARY KEY,
                parent_org_id VARCHAR NOT NULL DEFAULT '',
                name          VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata      JSONB NOT NULL DEFAULT '{}'::jsonb
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_fed_org_tenant ON federated_orgs(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m014 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        await conn.execute("DROP TABLE IF EXISTS federated_orgs")
        await conn.execute("DROP TABLE IF EXISTS audit_chain_records")
        await conn.execute("DROP TABLE IF EXISTS runtime_registry")
    except Exception as exc:  # pragma: no cover
        log.warning("m014 down fallback", error=repr(exc))


migration = Migration(id="m014_enterprise_scale", description="Enterprise scale: runtime registry, audit chain, federation", up=up, down=down)
