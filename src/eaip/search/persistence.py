"""PostgreSQL-backed persistence for search history and saved searches."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection


class PostgresSearchRepository:
    """Persists recent and saved searches to PostgreSQL with tenant isolation."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    async def list_recent(
        self, tenant_id: str, user_id: str | None, limit: int = 10,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            "SELECT query, category, timestamp FROM search_recent "
            "WHERE tenant_id = $1 AND ($2::text IS NULL OR user_id = $2) "
            "ORDER BY timestamp DESC LIMIT $3",
            tenant_id, user_id, limit,
        )
        return [
            {
                "id": f"recent-{uuid.uuid4().hex[:8]}",
                "query": row["query"],
                "category": row["category"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    async def save_recent(
        self, tenant_id: str, user_id: str | None, query: str, category: str,
    ) -> str:
        search_id = f"srch-{uuid.uuid4().hex[:8]}"
        await self._db.execute(
            "INSERT INTO search_recent (id, tenant_id, user_id, query, category, timestamp) "
            "VALUES ($1, $2, $3, $4, $5, NOW())",
            search_id, tenant_id, user_id, query, category,
        )
        await self._db.execute(
            "DELETE FROM search_recent WHERE tenant_id = $1 "
            "AND ($2::text IS NULL OR user_id = $2) "
            "AND id NOT IN (SELECT id FROM (SELECT id FROM search_recent "
            "WHERE tenant_id = $1 AND ($2::text IS NULL OR user_id = $2) "
            "ORDER BY timestamp DESC LIMIT 100) AS keep)",
            tenant_id, user_id,
        )
        return search_id

    async def list_saved(
        self, tenant_id: str, user_id: str | None,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            "SELECT id, name, query, category, filters, created_at "
            "FROM search_saved WHERE tenant_id = $1 "
            "AND ($2::text IS NULL OR user_id = $2) "
            "ORDER BY created_at DESC",
            tenant_id, user_id,
        )
        return [
            {
                "id": row["id"],
                "query": row["query"],
                "name": row["name"],
                "category": row["category"],
                "filters": row["filters"] or {},
                "timestamp": row["created_at"],
            }
            for row in rows
        ]

    async def save_saved(
        self, tenant_id: str, user_id: str | None, name: str, query: str,
        category: str, filters: dict[str, Any],
    ) -> str:
        search_id = f"svd-{uuid.uuid4().hex[:8]}"
        import json
        await self._db.execute(
            "INSERT INTO search_saved (id, tenant_id, user_id, name, query, category, filters, created_at) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())",
            search_id, tenant_id, user_id, name, query, category, json.dumps(filters),
        )
        return search_id

    async def delete_saved(
        self, tenant_id: str, user_id: str | None, search_id: str,
    ) -> bool:
        result = await self._db.execute(
            "DELETE FROM search_saved WHERE tenant_id = $1 "
            "AND ($2::text IS NULL OR user_id = $2) AND id = $3",
            tenant_id, user_id, search_id,
        )
        return result != "DELETE 0"
