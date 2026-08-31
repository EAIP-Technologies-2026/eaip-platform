from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m019")


async def up(conn) -> None:
    log.info("Running migration m019_m2_m3: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id   VARCHAR NOT NULL,
                organization_id VARCHAR NOT NULL,
                target          VARCHAR NOT NULL DEFAULT '',
                horizon         VARCHAR NOT NULL DEFAULT '7d',
                predicted_value TEXT,
                confidence      FLOAT NOT NULL DEFAULT 0.5,
                status          VARCHAR NOT NULL DEFAULT 'predicted',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (prediction_id, organization_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_pred_org ON predictions(organization_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_pred_target ON predictions(target)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS event_intelligence (
                event_id        VARCHAR NOT NULL,
                organization_id VARCHAR NOT NULL,
                type            VARCHAR NOT NULL DEFAULT 'generic',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (event_id, organization_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_evt_org ON event_intelligence(organization_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS self_corrections (
                correction_id   VARCHAR NOT NULL,
                organization_id VARCHAR NOT NULL,
                diagnosis       VARCHAR NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (correction_id, organization_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_corr_org ON self_corrections(organization_id)")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workforce_teams (
                team_id         VARCHAR NOT NULL,
                organization_id VARCHAR NOT NULL,
                goal            TEXT NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (team_id, organization_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_team_org ON workforce_teams(organization_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m019 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("workforce_teams", "self_corrections", "event_intelligence", "predictions"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m019 down fallback", error=repr(exc))


migration = Migration(id="m019_m2_m3_intelligence_reliability", description="M2/M3: predictions, events, self-corrections, workforce teams", up=up, down=down)
