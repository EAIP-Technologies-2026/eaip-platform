from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m025")


async def up(conn) -> None:
    log.info("Running migration m025_m2_persistence: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m2_predictions (
                prediction_id   VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (prediction_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m2_pred_tenant ON m2_predictions(tenant_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m2_radar (
                radar_id        VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (radar_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m2_radar_tenant ON m2_radar(tenant_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m2_briefings (
                briefing_id     VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (briefing_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m2_brief_tenant ON m2_briefings(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m025 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("m2_briefings", "m2_radar", "m2_predictions"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m025 down fallback", error=repr(exc))


migration = Migration(id="m025_m2_persistence", description="M2 durable store: predictions, risk radar, briefings", up=up, down=down)
