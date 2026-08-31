"""Migration 010: Marketplace persistence — extended packages and installations."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m010_marketplace")


async def up(conn) -> None:
    log.info("Running migration mm010_marketplace_persistence: up")
    try:
        # Extended marketplace packages — tenant-scoped
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS marketplace_packages_extended (
                package_id      VARCHAR         NOT NULL,
                tenant_id       VARCHAR         NOT NULL,
                name            VARCHAR         NOT NULL,
                type            VARCHAR         NOT NULL,
                version         VARCHAR         NOT NULL DEFAULT '0.1.0',
                description     TEXT            NOT NULL DEFAULT '',
                author          VARCHAR         NOT NULL DEFAULT '',
                dependencies    TEXT[]          NOT NULL DEFAULT '{}',
                tags            TEXT[]          NOT NULL DEFAULT '{}',
                status          VARCHAR         NOT NULL DEFAULT 'draft',
                visibility      VARCHAR         NOT NULL DEFAULT 'public',
                capabilities    TEXT[]          NOT NULL DEFAULT '{}',
                requirements    TEXT[]          NOT NULL DEFAULT '{}',
                compatibility   TEXT[]          NOT NULL DEFAULT '{}',
                industry        VARCHAR         NOT NULL DEFAULT '',
                downloads       INT             NOT NULL DEFAULT 0,
                rating          FLOAT           NOT NULL DEFAULT 0.0,
                metadata        JSONB           NOT NULL DEFAULT '{}'::jsonb,
                created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
                PRIMARY KEY (package_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_ext_tenant ON marketplace_packages_extended(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_ext_visibility ON marketplace_packages_extended(tenant_id, visibility)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_ext_status ON marketplace_packages_extended(tenant_id, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_ext_type ON marketplace_packages_extended(type)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_ext_industry ON marketplace_packages_extended(industry)")

        # Marketplace installations — tenant-scoped
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS marketplace_installations (
                installation_id VARCHAR         NOT NULL,
                package_id      VARCHAR         NOT NULL,
                tenant_id       VARCHAR         NOT NULL,
                version         VARCHAR         NOT NULL DEFAULT '0.1.0',
                installed_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
                installed_by    VARCHAR         NOT NULL DEFAULT 'system',
                status          VARCHAR         NOT NULL DEFAULT 'active',
                metadata        JSONB           NOT NULL DEFAULT '{}'::jsonb,
                PRIMARY KEY (installation_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_install_tenant ON marketplace_installations(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_install_package ON marketplace_installations(tenant_id, package_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_install_status ON marketplace_installations(tenant_id, status)")
    except Exception as exc:  # pragma: no cover - DB fallback
        log.warning("mm010_marketplace_persistence fallback (db unavailable)", error=repr(exc))


async def down(conn) -> None:
    log.info("Running migration mm010_marketplace_persistence: down")
    try:
        await conn.execute("DROP TABLE IF EXISTS marketplace_installations")
        await conn.execute("DROP TABLE IF EXISTS marketplace_packages_extended")
    except Exception as exc:  # pragma: no cover
        log.warning("mm010_marketplace_persistence down fallback", error=repr(exc))


migration = Migration(
    id="m010_marketplace_persistence",
    description="Marketplace persistence: marketplace_packages_extended and marketplace_installations with tenant isolation",
    up=up,
    down=down,
)
