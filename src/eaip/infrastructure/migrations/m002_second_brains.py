"""Second Brain persistence — durable store for governed brains.

Reuses the existing EAIP PostgreSQL + asyncpg migration pattern (no ORM).

The Brain domain is stored as a single row. Structured collections
(objectives, rules, tools, knowledge sources, recommendations, mission ids,
memory ids, activity) are persisted as JSONB to preserve existing domain
semantics without over-normalizing.
"""

from __future__ import annotations

from eaip.infrastructure.db.migrations import Migration


async def up(conn) -> None:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS second_brains (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            business_function TEXT NOT NULL DEFAULT '',
            owner_id TEXT NOT NULL,
            organization_id TEXT,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('draft','active','archived','disabled')),
            objectives JSONB NOT NULL DEFAULT '[]',
            instructions TEXT NOT NULL DEFAULT '',
            knowledge_sources JSONB NOT NULL DEFAULT '[]',
            rules JSONB NOT NULL DEFAULT '[]',
            tools JSONB NOT NULL DEFAULT '[]',
            approval_required BOOLEAN NOT NULL DEFAULT TRUE,
            recommendations JSONB NOT NULL DEFAULT '[]',
            mission_ids JSONB NOT NULL DEFAULT '[]',
            memory_ids JSONB NOT NULL DEFAULT '[]',
            activity JSONB NOT NULL DEFAULT '[]',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_second_brains_owner ON second_brains(owner_id)")
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_second_brains_org ON second_brains(organization_id)"
    )


async def down(conn) -> None:
    await conn.execute("DROP TABLE IF EXISTS second_brains")


migration = Migration(
    id="002_second_brains",
    description="Create second_brains table for durable governed Brain state",
    up=up,
    down=down,
)
