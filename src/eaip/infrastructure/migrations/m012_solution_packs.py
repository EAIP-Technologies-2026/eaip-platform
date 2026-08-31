from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m012")


async def up(conn) -> None:
    log.info("Running migration m012_solution_packs: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS solution_pack_installations (
                installation_id VARCHAR NOT NULL,
                pack_id         VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                industry        VARCHAR NOT NULL,
                status          VARCHAR NOT NULL DEFAULT 'installed',
                installed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                config          JSONB NOT NULL DEFAULT '{}'::jsonb,
                PRIMARY KEY (installation_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sp_install_tenant ON solution_pack_installations(tenant_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS onboarding_sessions (
                session_id      VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                company_name    VARCHAR NOT NULL,
                industry        VARCHAR NOT NULL DEFAULT '',
                pack_id         VARCHAR NOT NULL DEFAULT '',
                status          VARCHAR NOT NULL DEFAULT 'pending',
                progress        INT NOT NULL DEFAULT 0,
                steps           TEXT[] NOT NULL DEFAULT '{}',
                current_step    VARCHAR NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
                PRIMARY KEY (session_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_onboarding_tenant ON onboarding_sessions(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m012_solution_packs fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        await conn.execute("DROP TABLE IF EXISTS onboarding_sessions")
        await conn.execute("DROP TABLE IF EXISTS solution_pack_installations")
    except Exception as exc:  # pragma: no cover
        log.warning("m012 down fallback", error=repr(exc))


migration = Migration(id="m012_solution_packs", description="Solution packs + onboarding sessions", up=up, down=down)
