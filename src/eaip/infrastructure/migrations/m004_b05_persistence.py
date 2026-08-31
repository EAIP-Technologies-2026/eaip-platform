"""B05 persistence — memory items, knowledge graph, and search history tables.

Adds durable storage tables required by BATCH 05 (Brain / Knowledge / Memory):

- ``memory_items`` — persistent store for MemoryEngine items (PostgreSQL backed
  so memory survives process restarts, with tenant_id isolation).
- ``kgraph_nodes`` / ``kgraph_edges`` — knowledge graph entities and
  relationships with tenant scoping.
- ``search_recent`` / ``search_saved`` — recent and saved search persistence
  (replacing the in-memory lists in the search persistence router).
"""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration


async def up(conn) -> None:
    # ── Memory items (durable memory persistence) ────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_items (
            memory_id       TEXT        NOT NULL,
            tenant_id       TEXT        NOT NULL,
            user_id         TEXT,
            session_id      TEXT,
            application_id  TEXT,
            memory_type     TEXT        NOT NULL,
            domain          TEXT        NOT NULL DEFAULT 'personal',
            content         TEXT        NOT NULL,
            content_summary TEXT        NOT NULL DEFAULT '',
            importance      FLOAT       NOT NULL DEFAULT 0.5,
            confidence      FLOAT       NOT NULL DEFAULT 1.0,
            sensitivity     TEXT        NOT NULL DEFAULT 'informational',
            source          TEXT        NOT NULL DEFAULT 'conductor',
            provenance      TEXT        NOT NULL DEFAULT 'user_explicit',
            retention_policy TEXT       NOT NULL DEFAULT 'standard',
            status          TEXT        NOT NULL DEFAULT 'active',
            parent_id       TEXT,
            related_ids     JSONB       NOT NULL DEFAULT '[]',
            tags            JSONB       NOT NULL DEFAULT '[]',
            metadata        JSONB       NOT NULL DEFAULT '{}',
            embedding       JSONB,
            version         INT         NOT NULL DEFAULT 1,
            access_count    INT         NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            accessed_at     TIMESTAMPTZ,
            expires_at      TIMESTAMPTZ,
            PRIMARY KEY (memory_id, tenant_id)
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_items_tenant ON memory_items(tenant_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_items_scope ON memory_items"
        "(tenant_id, user_id, session_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_items_type_status ON memory_items"
        "(tenant_id, memory_type, status)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_items_expires ON memory_items(expires_at)"
        " WHERE status = 'active'"
    )

    # ── Knowledge graph nodes (entities) ──────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kgraph_nodes (
            id             TEXT        NOT NULL,
            tenant_id      TEXT        NOT NULL,
            type           TEXT        NOT NULL,
            name           TEXT        NOT NULL,
            description    TEXT        NOT NULL DEFAULT '',
            properties     JSONB       NOT NULL DEFAULT '{}',
            source         TEXT        NOT NULL DEFAULT '',
            confidence     FLOAT       NOT NULL DEFAULT 1.0,
            metadata       JSONB       NOT NULL DEFAULT '{}',
            tags           JSONB       NOT NULL DEFAULT '[]',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kgraph_nodes_tenant ON kgraph_nodes(tenant_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kgraph_nodes_type ON kgraph_nodes(tenant_id, type)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kgraph_nodes_name ON kgraph_nodes(tenant_id, name)"
    )

    # ── Knowledge graph edges (relationships) ─────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kgraph_edges (
            id                 TEXT        NOT NULL,
            tenant_id          TEXT        NOT NULL,
            type               TEXT        NOT NULL,
            source_entity_id   TEXT        NOT NULL,
            target_entity_id   TEXT        NOT NULL,
            properties         JSONB       NOT NULL DEFAULT '{}',
            weight             FLOAT       NOT NULL DEFAULT 1.0,
            bidirectional      BOOLEAN     NOT NULL DEFAULT FALSE,
            metadata           JSONB       NOT NULL DEFAULT '{}',
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kgraph_edges_tenant ON kgraph_edges(tenant_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kgraph_edges_type ON kgraph_edges(tenant_id, type)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kgraph_edges_source ON kgraph_edges"
        "(tenant_id, source_entity_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_kgraph_edges_target ON kgraph_edges"
        "(tenant_id, target_entity_id)"
    )

    # ── Search history (recent + saved) ───────────────────────────────
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS search_recent (
            id          TEXT        NOT NULL,
            tenant_id   TEXT        NOT NULL,
            user_id     TEXT,
            query       TEXT        NOT NULL,
            category    TEXT        NOT NULL DEFAULT '',
            timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_search_recent_tenant ON search_recent(tenant_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_search_recent_ts ON search_recent(tenant_id, timestamp DESC)"
    )

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS search_saved (
            id          TEXT        NOT NULL,
            tenant_id   TEXT        NOT NULL,
            user_id     TEXT,
            name        TEXT        NOT NULL,
            query       TEXT        NOT NULL,
            category    TEXT        NOT NULL DEFAULT '',
            filters     JSONB       NOT NULL DEFAULT '{}',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, tenant_id)
        )
    """)
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_search_saved_tenant ON search_saved(tenant_id)"
    )
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_search_saved_user ON search_saved(tenant_id, user_id)"
    )


async def down(conn) -> None:
    await conn.execute("DROP TABLE IF EXISTS search_saved")
    await conn.execute("DROP TABLE IF EXISTS search_recent")
    await conn.execute("DROP TABLE IF EXISTS kgraph_edges")
    await conn.execute("DROP TABLE IF EXISTS kgraph_nodes")
    await conn.execute("DROP TABLE IF EXISTS memory_items")


migration = Migration(
    id="004_b05_persistence",
    description="B05: create memory_items, kgraph_nodes, kgraph_edges, search_recent, search_saved tables",
    up=up,
    down=down,
    dependencies=("003_persistence_foundation",),
)
