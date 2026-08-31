"""M5 Migration — learning, audit, governance tables."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.migrations.m021")


async def up(conn) -> None:
    log.info("Running migration m021_learning_audit_governance: up")
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_records (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                source_type     VARCHAR NOT NULL,
                source_id       VARCHAR NOT NULL DEFAULT '',
                observation     JSONB NOT NULL DEFAULT '{}',
                evaluation      JSONB NOT NULL DEFAULT '{}',
                proposed_learning VARCHAR NOT NULL DEFAULT '',
                confidence      FLOAT NOT NULL DEFAULT 0.0,
                applicability   VARCHAR NOT NULL DEFAULT '',
                scope           VARCHAR NOT NULL DEFAULT '',
                status          VARCHAR NOT NULL DEFAULT 'proposed',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                activated_at    TIMESTAMPTZ,
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_lr_tenant ON learning_records(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_lr_source ON learning_records(source_type)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id                  VARCHAR NOT NULL,
                tenant_id           VARCHAR NOT NULL,
                learning_record_id  VARCHAR NOT NULL DEFAULT '',
                title               VARCHAR NOT NULL DEFAULT '',
                description         TEXT NOT NULL DEFAULT '',
                evidence            JSONB NOT NULL DEFAULT '[]',
                confidence          FLOAT NOT NULL DEFAULT 0.0,
                applicability_scope VARCHAR NOT NULL DEFAULT '',
                status              VARCHAR NOT NULL DEFAULT 'proposed',
                approval_id         VARCHAR NOT NULL DEFAULT '',
                effective_date      TIMESTAMPTZ,
                supersedes          VARCHAR NOT NULL DEFAULT '',
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_lesson_tenant ON lessons(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS adaptation_proposals (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                lesson_id       VARCHAR NOT NULL DEFAULT '',
                target_type     VARCHAR NOT NULL DEFAULT '',
                target_id       VARCHAR NOT NULL DEFAULT '',
                proposed_change JSONB NOT NULL DEFAULT '{}',
                risk_level      VARCHAR NOT NULL DEFAULT 'low',
                status          VARCHAR NOT NULL DEFAULT 'proposed',
                approval_id     VARCHAR NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_adapt_tenant ON adaptation_proposals(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback_records (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                source_type     VARCHAR NOT NULL,
                source_id       VARCHAR NOT NULL DEFAULT '',
                actual_outcome  JSONB NOT NULL DEFAULT '{}',
                error           FLOAT NOT NULL DEFAULT 0.0,
                quality_score   FLOAT NOT NULL DEFAULT 0.0,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_fb_tenant ON feedback_records(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_proofs_v2 (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                execution_id    VARCHAR NOT NULL DEFAULT '',
                intent_hash    VARCHAR NOT NULL DEFAULT '',
                context_hash   VARCHAR NOT NULL DEFAULT '',
                policy_hash    VARCHAR NOT NULL DEFAULT '',
                model_hash     VARCHAR NOT NULL DEFAULT '',
                tool_hash      VARCHAR NOT NULL DEFAULT '',
                connector_hash VARCHAR NOT NULL DEFAULT '',
                input_hash     VARCHAR NOT NULL DEFAULT '',
                output_hash    VARCHAR NOT NULL DEFAULT '',
                timestamp      VARCHAR NOT NULL DEFAULT '',
                previous_hash  VARCHAR NOT NULL DEFAULT '',
                current_hash   VARCHAR NOT NULL DEFAULT '',
                chain_index    INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_ep_tenant ON execution_proofs_v2(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_ep_exec ON execution_proofs_v2(execution_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS proof_verifications (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                proof_id        VARCHAR NOT NULL DEFAULT '',
                verified        BOOLEAN NOT NULL DEFAULT FALSE,
                tampered        BOOLEAN NOT NULL DEFAULT FALSE,
                details         JSONB NOT NULL DEFAULT '{}',
                verified_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_pv_tenant ON proof_verifications(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_policies (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                name            VARCHAR NOT NULL DEFAULT '',
                version         INTEGER NOT NULL DEFAULT 1,
                conditions      JSONB NOT NULL DEFAULT '{}',
                effect          VARCHAR NOT NULL DEFAULT 'allow',
                priority        INTEGER NOT NULL DEFAULT 0,
                scope           VARCHAR NOT NULL DEFAULT '',
                status          VARCHAR NOT NULL DEFAULT 'active',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_gp_tenant ON governance_policies(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_decisions (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                who             VARCHAR NOT NULL DEFAULT '',
                what            VARCHAR NOT NULL DEFAULT '',
                why             TEXT NOT NULL DEFAULT '',
                decision        VARCHAR NOT NULL DEFAULT '',
                reason          TEXT NOT NULL DEFAULT '',
                policy_ids      JSONB NOT NULL DEFAULT '[]',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_gd_tenant ON governance_decisions(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_exceptions (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                policy_id       VARCHAR NOT NULL DEFAULT '',
                reason          TEXT NOT NULL DEFAULT '',
                approver        VARCHAR NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at      TIMESTAMPTZ,
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_ge_tenant ON governance_exceptions(tenant_id)")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS approval_requests (
                id              VARCHAR NOT NULL,
                tenant_id       VARCHAR NOT NULL,
                requester       VARCHAR NOT NULL DEFAULT '',
                target_type     VARCHAR NOT NULL DEFAULT '',
                target_id       VARCHAR NOT NULL DEFAULT '',
                reason          TEXT NOT NULL DEFAULT '',
                status          VARCHAR NOT NULL DEFAULT 'pending',
                approver        VARCHAR NOT NULL DEFAULT '',
                decision_reason TEXT NOT NULL DEFAULT '',
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                decided_at      TIMESTAMPTZ,
                expires_at      TIMESTAMPTZ,
                PRIMARY KEY (id, tenant_id)
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_ar_tenant ON approval_requests(tenant_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_ar_status ON approval_requests(status)")

    except Exception as exc:  # pragma: no cover
        log.warning("m021 fallback", error=repr(exc))


async def down(conn) -> None:
    try:
        for tbl in (
            "approval_requests",
            "governance_exceptions",
            "governance_decisions",
            "governance_policies",
            "proof_verifications",
            "execution_proofs_v2",
            "feedback_records",
            "adaptation_proposals",
            "lessons",
            "learning_records",
        ):
            await conn.execute(f"DROP TABLE IF EXISTS {tbl}")
    except Exception as exc:  # pragma: no cover
        log.warning("m021 down fallback", error=repr(exc))


migration = Migration(
    id="m021_learning_audit_governance",
    description="M5: learning records, lessons, adaptation proposals, feedback, execution proofs, governance policies, decisions, exceptions, approvals",
    up=up,
    down=down,
)
