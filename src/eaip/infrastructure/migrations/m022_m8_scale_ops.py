"""M8 Migration — runtime pools, workloads, regions, DR, incidents, residency."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m022")


async def up(conn) -> None:
    log.info("Running migration m022_m8_scale_ops: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m8_runtime_pools (
                pool_id     VARCHAR NOT NULL,
                tenant_id   VARCHAR NOT NULL,
                name        VARCHAR NOT NULL DEFAULT '',
                kind        VARCHAR NOT NULL DEFAULT 'general',
                capacity    INTEGER NOT NULL DEFAULT 10,
                region      VARCHAR NOT NULL DEFAULT 'us-east-1',
                runtimes    JSONB NOT NULL DEFAULT '[]',
                status      VARCHAR NOT NULL DEFAULT 'healthy',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (pool_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m8pool_tenant ON m8_runtime_pools(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m8_workloads (
                workload_id          VARCHAR NOT NULL,
                tenant_id            VARCHAR NOT NULL,
                priority             VARCHAR NOT NULL DEFAULT 'normal',
                workload_type        VARCHAR NOT NULL DEFAULT 'general',
                payload              JSONB NOT NULL DEFAULT '{}',
                required_capabilities JSONB NOT NULL DEFAULT '[]',
                region               VARCHAR NOT NULL DEFAULT 'us-east-1',
                status               VARCHAR NOT NULL DEFAULT 'queued',
                assigned_runtime     VARCHAR NOT NULL DEFAULT '',
                created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (workload_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m8wl_tenant ON m8_workloads(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m8_regions (
                region       VARCHAR NOT NULL PRIMARY KEY,
                deployment   VARCHAR NOT NULL DEFAULT 'primary',
                runtimes     JSONB NOT NULL DEFAULT '[]',
                data_locality VARCHAR NOT NULL DEFAULT 'us-east-1',
                status       VARCHAR NOT NULL DEFAULT 'active'
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m8_data_residency (
                policy_id         VARCHAR NOT NULL,
                tenant_id         VARCHAR NOT NULL,
                data_class        VARCHAR NOT NULL DEFAULT 'general',
                allowed_regions   JSONB NOT NULL DEFAULT '[]',
                allowed_models    JSONB NOT NULL DEFAULT '[]',
                allowed_connectors JSONB NOT NULL DEFAULT '[]',
                allowed_storage   JSONB NOT NULL DEFAULT '[]',
                created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (policy_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m8dr_tenant ON m8_data_residency(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m8_incidents (
                incident_id   VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                title         VARCHAR NOT NULL DEFAULT '',
                severity      VARCHAR NOT NULL DEFAULT 'medium',
                status        VARCHAR NOT NULL DEFAULT 'open',
                correlated_ids JSONB NOT NULL DEFAULT '[]',
                diagnosis     TEXT NOT NULL DEFAULT '',
                recommendations JSONB NOT NULL DEFAULT '[]',
                remediation   TEXT NOT NULL DEFAULT '',
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (incident_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m8inc_tenant ON m8_incidents(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m8_recovery_points (
                point_id            VARCHAR NOT NULL,
                tenant_id           VARCHAR NOT NULL,
                state_hash          VARCHAR NOT NULL DEFAULT '',
                recovery_objective  VARCHAR NOT NULL DEFAULT '',
                validated           BOOLEAN NOT NULL DEFAULT FALSE,
                created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (point_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m8rp_tenant ON m8_recovery_points(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m022 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("m8_recovery_points", "m8_incidents", "m8_data_residency", "m8_regions", "m8_workloads", "m8_runtime_pools"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m022 down fallback", error=repr(exc))


migration = Migration(id="m022_m8_scale_ops", description="M8: pools, workloads, regions, residency, incidents, DR", up=up, down=down)
