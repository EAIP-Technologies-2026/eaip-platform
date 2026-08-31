from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m016")


async def up(conn) -> None:
    log.info("Running migration m016_wave2_application_layer: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS digital_employees (
                employee_id   VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                name          VARCHAR NOT NULL,
                role          VARCHAR NOT NULL DEFAULT '',
                department    VARCHAR NOT NULL DEFAULT '',
                capabilities  TEXT[] NOT NULL DEFAULT '{}',
                availability  VARCHAR NOT NULL DEFAULT 'available',
                workload      FLOAT NOT NULL DEFAULT 0,
                status        VARCHAR NOT NULL DEFAULT 'active',
                risk_level    VARCHAR NOT NULL DEFAULT 'low',
                performance   JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (employee_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_digital_emp_tenant ON digital_employees(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_digital_emp_status ON digital_employees(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_digital_emp_created ON digital_employees(created_at)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workforce_assignments2 (
                assignment_id VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                employee_id   VARCHAR NOT NULL,
                task_id       VARCHAR NOT NULL DEFAULT '',
                status        VARCHAR NOT NULL DEFAULT 'pending',
                priority      INT NOT NULL DEFAULT 0,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (assignment_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_assign2_tenant ON workforce_assignments2(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_assign2_employee ON workforce_assignments2(employee_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_assign2_status ON workforce_assignments2(status)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS methodologies2 (
                methodology_id VARCHAR NOT NULL,
                tenant_id      VARCHAR NOT NULL,
                name           VARCHAR NOT NULL,
                version        VARCHAR NOT NULL DEFAULT '1.0.0',
                category       VARCHAR NOT NULL DEFAULT 'reasoning',
                provider       VARCHAR NOT NULL DEFAULT 'eaip',
                lifecycle_status VARCHAR NOT NULL DEFAULT 'active',
                benchmark_score FLOAT NOT NULL DEFAULT 0,
                created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (methodology_id, tenant_id, version)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_method2_tenant ON methodologies2(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_method2_category ON methodologies2(category)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_method2_status ON methodologies2(lifecycle_status)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS document_records (
                document_id   VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                source        VARCHAR NOT NULL DEFAULT '',
                version       VARCHAR NOT NULL DEFAULT '1.0.0',
                status        VARCHAR NOT NULL DEFAULT 'pending',
                ocr_provider  VARCHAR NOT NULL DEFAULT 'local',
                classification VARCHAR NOT NULL DEFAULT 'general',
                confidence    FLOAT NOT NULL DEFAULT 0,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (document_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_docrec_tenant ON document_records(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_docrec_status ON document_records(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_docrec_document ON document_records(document_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS governed_systems (
                system_id     VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                type          VARCHAR NOT NULL DEFAULT 'model',
                name          VARCHAR NOT NULL,
                version       VARCHAR NOT NULL DEFAULT '1.0.0',
                risk          VARCHAR NOT NULL DEFAULT 'low',
                lifecycle     VARCHAR NOT NULL DEFAULT 'draft',
                approval      VARCHAR NOT NULL DEFAULT 'pending',
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (system_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_govsys_tenant ON governed_systems(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_govsys_risk ON governed_systems(risk)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_govsys_type ON governed_systems(type)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS digital_twins (
                twin_id       VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                enterprise    VARCHAR NOT NULL DEFAULT 'apex',
                state         JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (twin_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_twins_tenant ON digital_twins(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_twins_enterprise ON digital_twins(enterprise)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scenarios2 (
                scenario_id   VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                name          VARCHAR NOT NULL,
                baseline_state JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (scenario_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scen2_tenant ON scenarios2(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_scen2_created ON scenarios2(created_at)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS operational_insights (
                insight_id    VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                type          VARCHAR NOT NULL DEFAULT 'anomaly',
                severity      VARCHAR NOT NULL DEFAULT 'medium',
                status        VARCHAR NOT NULL DEFAULT 'open',
                confidence    FLOAT NOT NULL DEFAULT 0.5,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (insight_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_insight_tenant ON operational_insights(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_insight_severity ON operational_insights(severity)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_insight_status ON operational_insights(status)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS improvement_proposals (
                proposal_id   VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                source        VARCHAR NOT NULL DEFAULT 'manual',
                status        VARCHAR NOT NULL DEFAULT 'proposed',
                risk          VARCHAR NOT NULL DEFAULT 'low',
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (proposal_id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_improve_tenant ON improvement_proposals(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_improve_status ON improvement_proposals(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_improve_source ON improvement_proposals(source)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS decision_simulations (
                id            VARCHAR NOT NULL,
                tenant_id     VARCHAR NOT NULL,
                decision_id   VARCHAR NOT NULL,
                scenario_id   VARCHAR NOT NULL DEFAULT '',
                predicted     VARCHAR NOT NULL DEFAULT '',
                confidence    FLOAT NOT NULL DEFAULT 0.5,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_decisionsim_tenant ON decision_simulations(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_decisionsim_decision ON decision_simulations(decision_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_decisionsim_scenario ON decision_simulations(scenario_id)")

    except Exception as exc:  # pragma: no cover
        log.warning("m016 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in ("decision_simulations", "improvement_proposals", "operational_insights", "scenarios2", "digital_twins", "governed_systems", "document_records", "methodologies2", "workforce_assignments2", "digital_employees"):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m016 down fallback", error=repr(exc))


migration = Migration(id="m016_wave2_application_layer", description="Wave 2 application layer: workforce, methodologies, documents, governance, twins, scenarios, insights, improvements, decision-simulation", up=up, down=down)
