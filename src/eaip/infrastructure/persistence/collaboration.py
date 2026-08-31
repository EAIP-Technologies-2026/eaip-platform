"""Persistence repository for B06 Collaboration Sessions."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence import _row_to_dict, _TenantRepository


class CollaborationRepository(_TenantRepository):
    """Tenant-scoped durable storage for collaboration sessions."""

    async def create(self, session: dict[str, Any]) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            INSERT INTO collaboration_sessions
                (id, tenant_id, name, type, status, agents, goal, metadata,
                 result, created_at, started_at, completed_at)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8::jsonb, $9::jsonb, $10, $11, $12)
            ON CONFLICT (id, tenant_id) DO NOTHING
            """,
            session["id"],
            session.get("tenant_id", "default"),
            session["name"],
            session.get("type", "sequential"),
            session.get("status", "pending"),
            json.dumps(session.get("agents", [])),
            session.get("goal", ""),
            json.dumps(session.get("metadata", {})),
            json.dumps(session.get("result")) if session.get("result") else None,
            session.get("created_at", datetime.utcnow()),
            session.get("started_at"),
            session.get("completed_at"),
        )

    async def get(self, session_id: str, tenant_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, tenant_id, name, type, status, agents, goal, metadata,
                   result, created_at, started_at, completed_at
            FROM collaboration_sessions WHERE id = $1 AND tenant_id = $2
            """,
            session_id,
            tenant_id,
        )
        return _row_to_dict(row, {"agents", "metadata", "result"}) if row else None

    async def update(self, session_id: str, tenant_id: str, updates: dict[str, Any]) -> None:
        self._require_db()
        set_clauses = []
        params = [session_id, tenant_id]

        for key, value in updates.items():
            if key in ("id", "tenant_id", "created_at"):
                continue
            params.append(json.dumps(value) if isinstance(value, (list, dict)) else value)
            set_clauses.append(f"{key} = ${len(params)}" + ("::jsonb" if isinstance(value, (list, dict)) else ""))

        if not set_clauses:
            return

        query = f"""
            UPDATE collaboration_sessions
            SET {', '.join(set_clauses)}
            WHERE id = $1 AND tenant_id = $2
        """
        await DatabaseConnection.execute(query, *params)

    async def delete(self, session_id: str, tenant_id: str) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            UPDATE collaboration_sessions
            SET deleted_at = NOW()
            WHERE id = $1 AND tenant_id = $2
            """,
            session_id,
            tenant_id,
        )

    async def list_sessions(
        self, tenant_id: str, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        self._require_db()
        clauses = ["tenant_id = $1", "deleted_at IS NULL"]
        params: list[Any] = [tenant_id]

        if status:
            params.append(status)
            clauses.append(f"status = ${len(params)}")

        where = f"WHERE {' AND '.join(clauses)}"
        params.append(limit)

        rows = await DatabaseConnection.fetch(
            f"""
            SELECT id, tenant_id, name, type, status, agents, goal, metadata,
                   result, created_at, started_at, completed_at
            FROM collaboration_sessions
            {where}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [_row_to_dict(row, {"agents", "metadata", "result"}) for row in rows]
