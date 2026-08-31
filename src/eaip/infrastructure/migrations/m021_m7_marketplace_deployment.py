"""M7 Migration — marketplace artifacts, deployment packs, sandbox, configs, onboarding."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m021")


async def up(conn) -> None:
    log.info("Running migration m021_m7_marketplace_deployment: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m7_artifacts (
                artifact_id     VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                name            VARCHAR NOT NULL DEFAULT '',
                artifact_type   VARCHAR NOT NULL DEFAULT 'agent',
                version         VARCHAR NOT NULL DEFAULT '1.0.0',
                publisher       VARCHAR NOT NULL DEFAULT '',
                tenant_scope    VARCHAR NOT NULL DEFAULT 'global',
                capabilities    JSONB NOT NULL DEFAULT '[]',
                dependencies    JSONB NOT NULL DEFAULT '[]',
                compatibility   JSONB NOT NULL DEFAULT '[]',
                permissions     JSONB NOT NULL DEFAULT '[]',
                risk_class      VARCHAR NOT NULL DEFAULT 'low',
                signature       VARCHAR NOT NULL DEFAULT '',
                trust_state     VARCHAR NOT NULL DEFAULT 'unverified',
                lifecycle_state VARCHAR NOT NULL DEFAULT 'draft',
                description     TEXT NOT NULL DEFAULT '',
                tags            JSONB NOT NULL DEFAULT '[]',
                metadata        JSONB NOT NULL DEFAULT '{}',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (artifact_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m7art_tenant ON m7_artifacts(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m7art_type ON m7_artifacts(artifact_type)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m7_deployment_packs (
                pack_id         VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                name            VARCHAR NOT NULL DEFAULT '',
                version         VARCHAR NOT NULL DEFAULT '1.0.0',
                industry        VARCHAR NOT NULL DEFAULT 'general',
                base_pack_id    VARCHAR NOT NULL DEFAULT '',
                artifacts       JSONB NOT NULL DEFAULT '[]',
                agents          JSONB NOT NULL DEFAULT '[]',
                workflows       JSONB NOT NULL DEFAULT '[]',
                missions        JSONB NOT NULL DEFAULT '[]',
                policies        JSONB NOT NULL DEFAULT '[]',
                connectors      JSONB NOT NULL DEFAULT '[]',
                dashboards      JSONB NOT NULL DEFAULT '[]',
                kpis            JSONB NOT NULL DEFAULT '[]',
                methodologies   JSONB NOT NULL DEFAULT '[]',
                simulations     JSONB NOT NULL DEFAULT '[]',
                terminology     JSONB NOT NULL DEFAULT '{}',
                governance      JSONB NOT NULL DEFAULT '{}',
                onboarding_state JSONB NOT NULL DEFAULT '{}',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (pack_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m7pack_tenant ON m7_deployment_packs(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m7_sandbox_installations (
                installation_id VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                artifact_id     VARCHAR NOT NULL DEFAULT '',
                status          VARCHAR NOT NULL DEFAULT 'pending',
                verified        BOOLEAN NOT NULL DEFAULT FALSE,
                dependency_check JSONB NOT NULL DEFAULT '{}',
                security_check  JSONB NOT NULL DEFAULT '{}',
                test_result     JSONB NOT NULL DEFAULT '{}',
                governance_check JSONB NOT NULL DEFAULT '{}',
                approval_required BOOLEAN NOT NULL DEFAULT FALSE,
                installed_at    TIMESTAMPTZ,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (installation_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m7sbox_tenant ON m7_sandbox_installations(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m7_deployment_configs (
                config_id       VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                environment     VARCHAR NOT NULL DEFAULT 'development',
                region          VARCHAR NOT NULL DEFAULT 'us-east-1',
                runtime         VARCHAR NOT NULL DEFAULT 'local-1',
                model_policy    JSONB NOT NULL DEFAULT '{}',
                connector_policy JSONB NOT NULL DEFAULT '{}',
                autonomy_policy JSONB NOT NULL DEFAULT '{}',
                governance_policy JSONB NOT NULL DEFAULT '{}',
                industry_config JSONB NOT NULL DEFAULT '{}',
                deployment_version VARCHAR NOT NULL DEFAULT '1.0.0',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (config_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m7cfg_tenant ON m7_deployment_configs(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS m7_onboarding_sessions (
                session_id      VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                company_name    VARCHAR NOT NULL DEFAULT '',
                industry        VARCHAR NOT NULL DEFAULT '',
                requirements    JSONB NOT NULL DEFAULT '{}',
                solution_pack_id VARCHAR NOT NULL DEFAULT '',
                agents          JSONB NOT NULL DEFAULT '[]',
                workflows       JSONB NOT NULL DEFAULT '[]',
                connectors      JSONB NOT NULL DEFAULT '[]',
                policies        JSONB NOT NULL DEFAULT '[]',
                users           JSONB NOT NULL DEFAULT '[]',
                roles           JSONB NOT NULL DEFAULT '[]',
                simulation_id   VARCHAR NOT NULL DEFAULT '',
                validation      JSONB NOT NULL DEFAULT '{}',
                status          VARCHAR NOT NULL DEFAULT 'created',
                current_step    VARCHAR NOT NULL DEFAULT 'company',
                progress        INTEGER NOT NULL DEFAULT 0,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (session_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_m7onb_tenant ON m7_onboarding_sessions(tenant_id)")
    except Exception as exc:  # pragma: no cover
        log.warning("m021 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("m7_onboarding_sessions", "m7_deployment_configs", "m7_sandbox_installations", "m7_deployment_packs", "m7_artifacts"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m021 down fallback", error=repr(exc))


migration = Migration(id="m021_m7_marketplace_deployment", description="M7: marketplace artifacts, deployment packs, sandbox, configs, onboarding", up=up, down=down)
