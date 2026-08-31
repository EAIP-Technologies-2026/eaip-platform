"""M6 migration — connector registry, model fabric, and routing tables."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m022")


async def up(conn) -> None:
    log.info("Running migration m022_connectors_model_fabric: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS connector_registry (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                connector_type VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description TEXT DEFAULT '',
                status VARCHAR NOT NULL DEFAULT 'inactive',
                credential_ref VARCHAR DEFAULT '',
                config JSONB DEFAULT '{}',
                capabilities JSONB DEFAULT '[]',
                health_status VARCHAR DEFAULT 'unknown',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_connector_registry_tenant ON connector_registry(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_connector_registry_type ON connector_registry(connector_type)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS connector_capabilities (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                connector_id VARCHAR NOT NULL,
                operations JSONB DEFAULT '[]',
                permissions JSONB DEFAULT '[]',
                data_classes JSONB DEFAULT '[]',
                data_classification VARCHAR DEFAULT 'internal',
                cost_estimate FLOAT DEFAULT 0.0,
                latency_estimate FLOAT DEFAULT 0.0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_connector_cap_tenant ON connector_capabilities(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_connector_cap_connector ON connector_capabilities(connector_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS connector_health (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                connector_id VARCHAR NOT NULL,
                availability FLOAT DEFAULT 0.0,
                latency_ms FLOAT DEFAULT 0.0,
                error_rate FLOAT DEFAULT 0.0,
                auth_status VARCHAR DEFAULT 'unknown',
                rate_limit_remaining INT DEFAULT -1,
                degradation_level VARCHAR DEFAULT 'none',
                circuit_state VARCHAR DEFAULT 'closed',
                checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_connector_health_tenant ON connector_health(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_connector_health_connector ON connector_health(connector_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS connector_permissions (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                connector_id VARCHAR NOT NULL,
                operation VARCHAR NOT NULL,
                allowed_roles JSONB DEFAULT '[]',
                data_classification VARCHAR DEFAULT 'internal',
                requires_approval BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_connector_perm_tenant ON connector_permissions(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS model_registry (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                provider VARCHAR NOT NULL,
                model_name VARCHAR NOT NULL,
                version VARCHAR DEFAULT '1.0.0',
                capabilities JSONB DEFAULT '[]',
                context_limit INT DEFAULT 4096,
                latency_avg_ms FLOAT DEFAULT 0.0,
                cost_per_1k_tokens FLOAT DEFAULT 0.0,
                quality_score FLOAT DEFAULT 0.8,
                availability FLOAT DEFAULT 1.0,
                privacy_level VARCHAR DEFAULT 'cloud',
                locality VARCHAR DEFAULT 'cloud',
                supported_tools JSONB DEFAULT '[]',
                supported_modalities JSONB DEFAULT '["text"]',
                status VARCHAR DEFAULT 'active',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_model_registry_tenant ON model_registry(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_model_registry_provider ON model_registry(provider)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS model_evaluations (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                model_id VARCHAR NOT NULL,
                task_type VARCHAR NOT NULL,
                quality_score FLOAT DEFAULT 0.0,
                latency_ms FLOAT DEFAULT 0.0,
                cost FLOAT DEFAULT 0.0,
                success BOOLEAN DEFAULT TRUE,
                evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_model_eval_tenant ON model_evaluations(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_model_eval_model ON model_evaluations(model_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS model_experiments (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                models JSONB DEFAULT '[]',
                task_type VARCHAR DEFAULT '',
                traffic_split JSONB DEFAULT '{}',
                status VARCHAR DEFAULT 'draft',
                winner VARCHAR DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_model_exp_tenant ON model_experiments(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS model_experiment_results (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                experiment_id VARCHAR NOT NULL,
                model_id VARCHAR NOT NULL,
                quality FLOAT DEFAULT 0.0,
                latency_ms FLOAT DEFAULT 0.0,
                cost FLOAT DEFAULT 0.0,
                success BOOLEAN DEFAULT TRUE,
                recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_model_exp_result_tenant ON model_experiment_results(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_model_exp_result_exp ON model_experiment_results(experiment_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS routing_decisions (
                id VARCHAR NOT NULL,
                tenant_id VARCHAR NOT NULL,
                task_type VARCHAR NOT NULL,
                requirements JSONB DEFAULT '{}',
                selected_model_id VARCHAR NOT NULL,
                reason TEXT DEFAULT '',
                alternatives JSONB DEFAULT '[]',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_routing_dec_tenant ON routing_decisions(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_routing_dec_model ON routing_decisions(selected_model_id)")

    except Exception as exc:  # pragma: no cover
        log.warning("m022 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in (
            "routing_decisions",
            "model_experiment_results",
            "model_experiments",
            "model_evaluations",
            "model_registry",
            "connector_permissions",
            "connector_health",
            "connector_capabilities",
            "connector_registry",
        ):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m022 down fallback", error=repr(exc))


migration = Migration(
    id="m022_connectors_model_fabric",
    description="M6 connector registry, model fabric, routing decisions",
    up=up,
    down=down,
)
