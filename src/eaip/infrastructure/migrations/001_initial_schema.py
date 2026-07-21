"""Initial production schema — all EAIP entities."""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration


async def up(conn) -> None:
    # ── Extensions ────────────────────────────────────────────────
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS uuid_ossp")

    # ── Organizations ─────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            member_count INT NOT NULL DEFAULT 0,
            metadata JSONB NOT NULL DEFAULT '{}',
            settings JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_organizations_deleted_at ON organizations(deleted_at)")

    # ── Users ─────────────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL DEFAULT '',
            roles TEXT[] NOT NULL DEFAULT '{}',
            avatar_url TEXT NOT NULL DEFAULT '',
            organization_id TEXT REFERENCES organizations(id),
            metadata JSONB NOT NULL DEFAULT '{}',
            preferences JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            last_login_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at)")

    # ── Auth Tokens ──────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id TEXT PRIMARY KEY,
            token_type TEXT NOT NULL,
            issuer TEXT NOT NULL DEFAULT 'eaip',
            subject TEXT NOT NULL,
            audience TEXT[] NOT NULL DEFAULT '{}',
            claims JSONB NOT NULL DEFAULT '{}',
            issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            not_before TIMESTAMPTZ,
            token_hash TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'expired', 'revoked', 'suspended'))
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_subject ON auth_tokens(subject)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_status ON auth_tokens(status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at)")

    # ── Agents ────────────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            version TEXT NOT NULL DEFAULT '0.1.0',
            tools TEXT[] NOT NULL DEFAULT '{}',
            llm_adapter TEXT NOT NULL DEFAULT '',
            max_steps INT NOT NULL DEFAULT 25,
            metadata JSONB NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft','registered','ready','running','paused','stopped','failed','archived')),
            organization_id TEXT REFERENCES organizations(id),
            created_by TEXT REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_org ON agents(organization_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_deleted_at ON agents(deleted_at)")

    # ── Agent Runs ────────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL REFERENCES agents(id),
            goal_text TEXT NOT NULL DEFAULT '',
            goal_constraints TEXT[] NOT NULL DEFAULT '{}',
            goal_metadata JSONB NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','running','completed','failed','cancelled')),
            result TEXT NOT NULL DEFAULT '',
            error TEXT,
            duration_ms FLOAT NOT NULL DEFAULT 0.0,
            steps JSONB NOT NULL DEFAULT '[]',
            plan JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_created ON agent_runs(created_at)")

    # ── Workflows ────────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            version TEXT NOT NULL DEFAULT '0.1.0',
            steps JSONB NOT NULL DEFAULT '[]',
            edges JSONB NOT NULL DEFAULT '[]',
            parallel_groups JSONB NOT NULL DEFAULT '[]',
            entry_point TEXT NOT NULL DEFAULT '',
            triggers JSONB NOT NULL DEFAULT '[]',
            timeout_config JSONB,
            metadata JSONB NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft','pending','running','paused','completed','failed','cancelled','timed_out','archived','published')),
            organization_id TEXT REFERENCES organizations(id),
            created_by TEXT REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            published_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_org ON workflows(organization_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_created ON workflows(created_at)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_deleted_at ON workflows(deleted_at)")

    # ── Workflow Versions ────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS workflow_versions (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
            version INT NOT NULL,
            steps JSONB NOT NULL DEFAULT '[]',
            edges JSONB NOT NULL DEFAULT '[]',
            viewport JSONB NOT NULL DEFAULT '{}',
            zoom FLOAT NOT NULL DEFAULT 1.0,
            pan_x FLOAT NOT NULL DEFAULT 0.0,
            pan_y FLOAT NOT NULL DEFAULT 0.0,
            variables JSONB NOT NULL DEFAULT '[]',
            secrets JSONB NOT NULL DEFAULT '[]',
            execution_settings JSONB NOT NULL DEFAULT '{}',
            retry_policy JSONB,
            tags TEXT[] NOT NULL DEFAULT '{}',
            labels TEXT[] NOT NULL DEFAULT '{}',
            message TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft','published','archived')),
            created_by TEXT REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (workflow_id, version)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_versions_workflow ON workflow_versions(workflow_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_versions_version ON workflow_versions(workflow_id, version)")

    # ── Workflow Runs ────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL REFERENCES workflows(id),
            definition_snapshot JSONB NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','running','paused','completed','failed','cancelled','timed_out')),
            context JSONB NOT NULL DEFAULT '{}',
            result TEXT NOT NULL DEFAULT '',
            error TEXT,
            step_records JSONB NOT NULL DEFAULT '[]',
            step_count INT NOT NULL DEFAULT 0,
            completed_count INT NOT NULL DEFAULT 0,
            failed_count INT NOT NULL DEFAULT 0,
            skipped_count INT NOT NULL DEFAULT 0,
            child_run_ids TEXT[] NOT NULL DEFAULT '{}',
            duration_ms FLOAT NOT NULL DEFAULT 0.0,
            triggered_by TEXT NOT NULL DEFAULT 'manual',
            triggered_by_type TEXT NOT NULL DEFAULT 'manual'
                CHECK (triggered_by_type IN ('schedule','manual','event','webhook')),
            state_machine_state TEXT NOT NULL DEFAULT 'pending',
            parent_run_id TEXT REFERENCES workflow_runs(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_runs_workflow ON workflow_runs(workflow_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_runs_status ON workflow_runs(status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_wf_runs_created ON workflow_runs(created_at)")

    # ── Missions ─────────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS missions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft','queued','running','completed','failed','cancelled')),
            agent_ids TEXT[] NOT NULL DEFAULT '{}',
            workflow_ids TEXT[] NOT NULL DEFAULT '{}',
            knowledge_collections TEXT[] NOT NULL DEFAULT '{}',
            metadata JSONB NOT NULL DEFAULT '{}',
            error TEXT,
            result TEXT NOT NULL DEFAULT '',
            duration_ms FLOAT NOT NULL DEFAULT 0.0,
            priority INT NOT NULL DEFAULT 0,
            organization_id TEXT REFERENCES organizations(id),
            created_by TEXT REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_missions_org ON missions(organization_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_missions_created ON missions(created_at)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_missions_deleted_at ON missions(deleted_at)")

    # ── Mission Executions ───────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS mission_executions (
            id TEXT PRIMARY KEY,
            mission_id TEXT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'queued'
                CHECK (status IN ('queued','running','completed','failed','cancelled')),
            steps JSONB NOT NULL DEFAULT '[]',
            error TEXT,
            result TEXT NOT NULL DEFAULT '',
            duration_ms FLOAT NOT NULL DEFAULT 0.0,
            triggered_by TEXT NOT NULL DEFAULT 'manual',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_mission_execs_mission ON mission_executions(mission_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_mission_execs_status ON mission_executions(status)")

    # ── Knowledge Collections ────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_collections (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            embedding_config JSONB NOT NULL DEFAULT '{}',
            chunking_config JSONB NOT NULL DEFAULT '{}',
            document_count INT NOT NULL DEFAULT 0,
            chunk_count INT NOT NULL DEFAULT 0,
            metadata JSONB NOT NULL DEFAULT '{}',
            organization_id TEXT REFERENCES organizations(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_collections_name ON knowledge_collections(name)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_collections_deleted_at ON knowledge_collections(deleted_at)")

    # ── Knowledge Documents ─────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id TEXT PRIMARY KEY,
            collection_id TEXT NOT NULL REFERENCES knowledge_collections(id) ON DELETE CASCADE,
            title TEXT NOT NULL DEFAULT '',
            format TEXT NOT NULL DEFAULT 'txt',
            source TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            metadata JSONB NOT NULL DEFAULT '{}',
            tags TEXT[] NOT NULL DEFAULT '{}',
            indexing_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (indexing_status IN ('pending','indexing','indexed','failed')),
            content_hash TEXT NOT NULL DEFAULT '',
            chunk_count INT NOT NULL DEFAULT 0,
            file_size BIGINT NOT NULL DEFAULT 0,
            version INT NOT NULL DEFAULT 1,
            organization_id TEXT REFERENCES organizations(id),
            created_by TEXT REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_docs_collection ON knowledge_documents(collection_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_docs_status ON knowledge_documents(indexing_status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_docs_deleted_at ON knowledge_documents(deleted_at)")

    # ── Deployments ──────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT NOT NULL DEFAULT '0.1.0',
            environment TEXT NOT NULL DEFAULT 'development'
                CHECK (environment IN ('development','staging','production')),
            config JSONB NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','deploying','deployed','failed','rolled_back')),
            organization_id TEXT REFERENCES organizations(id),
            created_by TEXT REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deployed_at TIMESTAMPTZ,
            rolled_back_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_deployments_environment ON deployments(environment)")

    # ── Audit Events ─────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            actor_id TEXT,
            actor_type TEXT NOT NULL DEFAULT 'user',
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            action TEXT NOT NULL,
            changes JSONB NOT NULL DEFAULT '{}',
            metadata JSONB NOT NULL DEFAULT '{}',
            organization_id TEXT REFERENCES organizations(id),
            ip_address TEXT NOT NULL DEFAULT '',
            user_agent TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_actor ON audit_events(actor_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_resource ON audit_events(resource_type, resource_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_created ON audit_events(created_at)")

    # ── Runtime Events ──────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS runtime_events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT '',
            payload JSONB NOT NULL DEFAULT '{}',
            metadata JSONB NOT NULL DEFAULT '{}',
            correlation_id TEXT,
            organization_id TEXT REFERENCES organizations(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_events_type ON runtime_events(event_type)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_events_source ON runtime_events(source)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_events_created ON runtime_events(created_at)")

    # ── Notifications ────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            type TEXT NOT NULL DEFAULT 'info'
                CHECK (type IN ('info','success','warning','error')),
            title TEXT NOT NULL,
            message TEXT NOT NULL DEFAULT '',
            channel TEXT NOT NULL DEFAULT 'global',
            read BOOLEAN NOT NULL DEFAULT FALSE,
            archived BOOLEAN NOT NULL DEFAULT FALSE,
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(user_id, read)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)")

    # ── Feature Flags ────────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS feature_flags (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            enabled BOOLEAN NOT NULL DEFAULT FALSE,
            description TEXT NOT NULL DEFAULT '',
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Platform Settings ────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS platform_settings (
            id TEXT PRIMARY KEY,
            key TEXT NOT NULL UNIQUE,
            value JSONB NOT NULL DEFAULT '{}',
            description TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ── Memory Metadata ─────────────────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_metadata (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            key TEXT NOT NULL,
            value TEXT NOT NULL DEFAULT '',
            type TEXT NOT NULL DEFAULT 'memory',
            importance FLOAT NOT NULL DEFAULT 0.5,
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (agent_id, key)
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_agent ON memory_metadata(agent_id)")


async def down(conn) -> None:
    tables = [
        "memory_metadata", "platform_settings", "feature_flags",
        "notifications", "runtime_events", "audit_events",
        "deployments", "knowledge_documents", "knowledge_collections",
        "mission_executions", "missions", "workflow_runs",
        "workflow_versions", "workflows", "agent_runs", "agents",
        "auth_tokens", "users", "organizations",
    ]
    for table in tables:
        await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")


migration = Migration(
    id="001_initial_schema",
    description="Create all production tables: organizations, users, auth, agents, workflows, missions, knowledge, deployments, audit, runtime events, notifications",
    up=up,
    down=down,
)
