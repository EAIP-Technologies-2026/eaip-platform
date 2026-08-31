"""M9 Migration — executive briefings, KPIs, department views."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m023")


async def up(conn) -> None:
    log.info("Running migration m023_m9_executive: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m9_briefings (
                briefing_id    VARCHAR NOT NULL,
                tenant_id      VARCHAR NOT NULL,
                what_changed   JSONB NOT NULL DEFAULT '[]',
                why            TEXT NOT NULL DEFAULT '',
                risks          JSONB NOT NULL DEFAULT '[]',
                opportunities  JSONB NOT NULL DEFAULT '[]',
                decisions      JSONB NOT NULL DEFAULT '[]',
                actions        JSONB NOT NULL DEFAULT '[]',
                forecast       JSONB NOT NULL DEFAULT '[]',
                recommendations JSONB NOT NULL DEFAULT '[]',
                created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (briefing_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m9brief_tenant ON m9_briefings(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m9_kpis (
                kpi_id      VARCHAR NOT NULL,
                tenant_id   VARCHAR NOT NULL,
                name        VARCHAR NOT NULL DEFAULT '',
                value       FLOAT NOT NULL DEFAULT 0,
                target      FLOAT NOT NULL DEFAULT 0,
                unit        VARCHAR NOT NULL DEFAULT '',
                trend       VARCHAR NOT NULL DEFAULT 'stable',
                department  VARCHAR NOT NULL DEFAULT '',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (kpi_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m9kpi_tenant ON m9_kpis(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m9_department_views (
                view_id     VARCHAR NOT NULL,
                tenant_id   VARCHAR NOT NULL,
                department  VARCHAR NOT NULL DEFAULT 'executive',
                industry    VARCHAR NOT NULL DEFAULT '',
                title       VARCHAR NOT NULL DEFAULT '',
                sections    JSONB NOT NULL DEFAULT '[]',
                kpis        JSONB NOT NULL DEFAULT '[]',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (view_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m9dept_tenant ON m9_department_views(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m023 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("m9_department_views", "m9_kpis", "m9_briefings"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m023 down fallback", error=repr(exc))


migration = Migration(id="m023_m9_executive", description="M9: briefings, KPIs, department views", up=up, down=down)
