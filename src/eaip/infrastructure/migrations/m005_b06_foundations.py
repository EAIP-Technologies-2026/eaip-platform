"""B06 workforce & automation foundations — goals, automations, templates.

Adds durable storage tables required by BATCH 06 (Workforce & Automation):

- ``goals`` — persistent store for BusinessGoal entities with objectives and KPIs.
- ``automation_rules`` — persistent store for trigger-based automation workflows.
- ``agent_templates`` — persistent store for reusable agent configurations.
- ``skills`` — persistent store for the Skill Registry.
- ``collaboration_sessions`` — persistent store for multi-agent coordination.
"""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration


async def up(conn) -> None:
    # ── Goals ──────────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id             TEXT        NOT NULL,
            tenant_id      TEXT        NOT NULL,
            name           TEXT        NOT NULL,
            description    TEXT        NOT NULL DEFAULT '',
            status         TEXT        NOT NULL DEFAULT 'draft',
            priority       TEXT        NOT NULL DEFAULT 'medium',
            owner          TEXT        NOT NULL DEFAULT '',
            kpis           JSONB       NOT NULL DEFAULT '[]',
            objectives     JSONB       NOT NULL DEFAULT '[]',
            deadline       TIMESTAMPTZ,
            tags           JSONB       NOT NULL DEFAULT '[]',
            metadata       JSONB       NOT NULL DEFAULT '{}',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at     TIMESTAMPTZ,
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_goals_tenant ON goals(tenant_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(tenant_id, status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_goals_owner ON goals(tenant_id, owner)")

    # ── Automation Rules ─────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS automation_rules (
            id             TEXT        NOT NULL,
            tenant_id      TEXT        NOT NULL,
            name           TEXT        NOT NULL,
            description    TEXT        NOT NULL DEFAULT '',
            status         TEXT        NOT NULL DEFAULT 'active',
            trigger_config JSONB       NOT NULL,
            action_config  JSONB       NOT NULL,
            conditions     JSONB       NOT NULL DEFAULT '[]',
            metadata       JSONB       NOT NULL DEFAULT '{}',
            created_by     TEXT        NOT NULL DEFAULT '',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at     TIMESTAMPTZ,
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_automation_tenant ON automation_rules(tenant_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_automation_status ON automation_rules(tenant_id, status)")

    # ── Agent Templates ──────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_templates (
            id             TEXT        NOT NULL,
            tenant_id      TEXT        NOT NULL,
            name           TEXT        NOT NULL,
            description    TEXT        NOT NULL DEFAULT '',
            version        TEXT        NOT NULL DEFAULT '0.1.0',
            spec           JSONB       NOT NULL,
            metadata       JSONB       NOT NULL DEFAULT '{}',
            created_by     TEXT        NOT NULL DEFAULT '',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at     TIMESTAMPTZ,
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_templates_tenant ON agent_templates(tenant_id)")

    # ── Skills ───────────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id             TEXT        NOT NULL,
            tenant_id      TEXT        NOT NULL,
            name           TEXT        NOT NULL,
            description    TEXT        NOT NULL DEFAULT '',
            version        TEXT        NOT NULL DEFAULT '0.1.0',
            status         TEXT        NOT NULL DEFAULT 'active',
            entry_point    TEXT        NOT NULL,
            parameters     JSONB       NOT NULL DEFAULT '{}',
            metadata       JSONB       NOT NULL DEFAULT '{}',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at     TIMESTAMPTZ,
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_skills_tenant ON skills(tenant_id)")

    # ── Collaboration Sessions ───────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS collaboration_sessions (
            id             TEXT        NOT NULL,
            tenant_id      TEXT        NOT NULL,
            name           TEXT        NOT NULL,
            type           TEXT        NOT NULL DEFAULT 'sequential',
            status         TEXT        NOT NULL DEFAULT 'pending',
            agents         JSONB       NOT NULL DEFAULT '[]',
            goal           TEXT        NOT NULL DEFAULT '',
            metadata       JSONB       NOT NULL DEFAULT '{}',
            result         JSONB,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at     TIMESTAMPTZ,
            completed_at   TIMESTAMPTZ,
            deleted_at     TIMESTAMPTZ,
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_collab_tenant ON collaboration_sessions(tenant_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_collab_status ON collaboration_sessions(tenant_id, status)")


async def down(conn) -> None:
    await conn.execute("DROP TABLE IF EXISTS collaboration_sessions")
    await conn.execute("DROP TABLE IF EXISTS skills")
    await conn.execute("DROP TABLE IF EXISTS agent_templates")
    await conn.execute("DROP TABLE IF EXISTS automation_rules")
    await conn.execute("DROP TABLE IF EXISTS goals")


migration = Migration(
    id="005_b06_foundations",
    description="B06: create goals, automation_rules, agent_templates, and skills tables",
    up=up,
    down=down,
)
