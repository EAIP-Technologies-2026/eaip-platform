"""M018 — M4 Strategy Foundation: strategic objectives, initiatives, constraints, themes, state, milestones, KPIs, risks, intelligence cycles, governance decisions."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m020")


async def up(conn) -> None:
    log.info("Running migration m020_strategy_foundation: up")
    try:
        # strategic objectives
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS strategic_objectives ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, title VARCHAR NOT NULL, "
            "description TEXT DEFAULT '', priority VARCHAR DEFAULT 'medium', "
            "status VARCHAR DEFAULT 'draft', owner VARCHAR DEFAULT '', "
            "time_horizon VARCHAR DEFAULT 'annual', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
            "valid_from TIMESTAMPTZ, valid_until TIMESTAMPTZ, supersedes VARCHAR, "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_obj_tenant ON strategic_objectives(tenant_id)")

        # strategic initiatives
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS strategic_initiatives ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, objective_id VARCHAR NOT NULL, "
            "title VARCHAR NOT NULL, description TEXT DEFAULT '', status VARCHAR DEFAULT 'planned', "
            "budget NUMERIC DEFAULT 0, owner VARCHAR DEFAULT '', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_ini_tenant ON strategic_initiatives(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_ini_obj ON strategic_initiatives(objective_id)")

        # strategic constraints
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS strategic_constraints ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, type VARCHAR NOT NULL, "
            "description TEXT DEFAULT '', severity VARCHAR DEFAULT 'medium', "
            "effective_from TIMESTAMPTZ, effective_until TIMESTAMPTZ, "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_con_tenant ON strategic_constraints(tenant_id)")

        # strategic themes
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS strategic_themes ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, name VARCHAR NOT NULL, "
            "description TEXT DEFAULT '', weight NUMERIC DEFAULT 1.0, "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_thm_tenant ON strategic_themes(tenant_id)")

        # strategic state
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS strategic_state ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, version INTEGER DEFAULT 1, "
            "objectives_snapshot JSONB DEFAULT '[]', rationale TEXT DEFAULT '', "
            "approval_id VARCHAR DEFAULT '', effective_date TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
            "supersedes VARCHAR, "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_state_tenant ON strategic_state(tenant_id)")

        # strategic milestones
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS strategic_milestones ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, initiative_id VARCHAR NOT NULL, "
            "title VARCHAR NOT NULL, target_date TIMESTAMPTZ, status VARCHAR DEFAULT 'pending', "
            "owner VARCHAR DEFAULT '', "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_ms_tenant ON strategic_milestones(tenant_id)")

        # strategic KPIs
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS strategic_kpis ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, objective_id VARCHAR NOT NULL, "
            "name VARCHAR NOT NULL, target NUMERIC DEFAULT 0, current NUMERIC DEFAULT 0, "
            "trend VARCHAR DEFAULT 'stable', "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_kpi_tenant ON strategic_kpis(tenant_id)")

        # strategic risks
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS strategic_risks ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, objective_id VARCHAR NOT NULL, "
            "description TEXT DEFAULT '', likelihood VARCHAR DEFAULT 'medium', "
            "impact VARCHAR DEFAULT 'medium', mitigation TEXT DEFAULT '', "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_strat_risk_tenant ON strategic_risks(tenant_id)")

        # intelligence cycles
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS intelligence_cycles ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, objective TEXT NOT NULL, "
            "context JSONB DEFAULT '{}', observations JSONB DEFAULT '[]', "
            "reasoning JSONB DEFAULT '{}', plan JSONB DEFAULT '{}', "
            "actions JSONB DEFAULT '[]', measurements JSONB DEFAULT '[]', "
            "reflection JSONB DEFAULT '{}', correction JSONB DEFAULT '{}', "
            "resulting_state JSONB DEFAULT '{}', status VARCHAR DEFAULT 'started', "
            "autonomy_level VARCHAR DEFAULT 'L2', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_intel_cycle_tenant ON intelligence_cycles(tenant_id)")

        # governance decisions
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS governance_decisions ("
            "id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, who VARCHAR NOT NULL, "
            "what VARCHAR NOT NULL, why TEXT DEFAULT '', data_ref VARCHAR DEFAULT '', "
            "system_ref VARCHAR DEFAULT '', action VARCHAR DEFAULT '', "
            "risk_level VARCHAR DEFAULT 'low', cost_estimate NUMERIC DEFAULT 0, "
            "autonomy_level VARCHAR DEFAULT 'L2', decision VARCHAR DEFAULT 'ALLOW', "
            "reason TEXT DEFAULT '', policy_ids JSONB DEFAULT '[]', "
            "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
            "PRIMARY KEY (id, tenant_id))"
        )
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_gov_dec_tenant ON governance_decisions(tenant_id)")

    except Exception as exc:  # pragma: no cover
        log.warning("m020 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in (
            "governance_decisions", "intelligence_cycles", "strategic_risks",
            "strategic_kpis", "strategic_milestones", "strategic_state",
            "strategic_themes", "strategic_constraints", "strategic_initiatives",
            "strategic_objectives",
        ):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m020 down fallback", error=repr(exc))


migration = Migration(
    id="m020_strategy_foundation",
    description="M4 Strategy Foundation: PSF, RIL, EGE, KCR tables",
    up=up,
    down=down,
)
