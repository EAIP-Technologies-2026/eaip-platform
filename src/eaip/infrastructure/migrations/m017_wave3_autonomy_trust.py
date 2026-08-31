from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m017")


async def up(conn) -> None:
    log.info("Running migration m017_wave3_autonomy_trust: up")
    try:
        await conn.execute("CREATE TABLE IF NOT EXISTS autonomy_policies (policy_id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, name VARCHAR NOT NULL, max_level VARCHAR NOT NULL DEFAULT 'L1', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (policy_id, tenant_id))")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_autonomy_tenant ON autonomy_policies(tenant_id)")
        await conn.execute("CREATE TABLE IF NOT EXISTS workflow_compositions (id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, goal TEXT NOT NULL, status VARCHAR NOT NULL DEFAULT 'draft', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (id, tenant_id))")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_compose_tenant ON workflow_compositions(tenant_id)")
        await conn.execute("CREATE TABLE IF NOT EXISTS marketplace_signatures (package_id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, signature VARCHAR NOT NULL, status VARCHAR NOT NULL DEFAULT 'published', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (package_id, tenant_id))")
        await conn.execute("CREATE TABLE IF NOT EXISTS execution_proofs (record_id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, execution_id VARCHAR NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (record_id, tenant_id))")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_proofs_tenant ON execution_proofs(tenant_id)")
        await conn.execute("CREATE TABLE IF NOT EXISTS federation_trust (trust_id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, from_org VARCHAR NOT NULL, to_org VARCHAR NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (trust_id, tenant_id))")
        await conn.execute("CREATE TABLE IF NOT EXISTS federation_delegations (delegation_id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, who VARCHAR NOT NULL, what VARCHAR NOT NULL, expires_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (delegation_id, tenant_id))")
        await conn.execute("CREATE TABLE IF NOT EXISTS simulation_branches (branch_id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, from_scenario VARCHAR NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (branch_id, tenant_id))")
        await conn.execute("CREATE TABLE IF NOT EXISTS onboarding_state (session_id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, status VARCHAR NOT NULL DEFAULT 'pending', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (session_id, tenant_id))")
        await conn.execute("CREATE TABLE IF NOT EXISTS cross_system_runs (run_id VARCHAR NOT NULL, tenant_id VARCHAR NOT NULL, status VARCHAR NOT NULL DEFAULT 'completed', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (run_id, tenant_id))")
    except Exception as exc:  # pragma: no cover
        log.warning("m017 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("cross_system_runs", "onboarding_state", "simulation_branches", "federation_delegations", "federation_trust", "execution_proofs", "marketplace_signatures", "workflow_compositions", "autonomy_policies"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m017 down fallback", error=repr(exc))


migration = Migration(id="m017_wave3_autonomy_trust", description="Wave 3 autonomy, trust, federation, simulation branching", up=up, down=down)
