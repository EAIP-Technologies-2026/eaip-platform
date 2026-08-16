"""Persistence repository for B06 Goals."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence import _row_to_dict, _TenantRepository


class GoalRepository(_TenantRepository):
    """Tenant-scoped durable storage for goals (``goals``)."""

    async def create(self, goal: dict[str, Any]) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            INSERT INTO goals
                (id, tenant_id, name, description, status, priority, owner,
                 kpis, objectives, deadline, tags, metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10, $11::jsonb, $12::jsonb, $13, $14)
            ON CONFLICT (id, tenant_id) DO NOTHING
            """,
            goal["id"],
            goal.get("tenant_id", "default"),
            goal["name"],
            goal.get("description", ""),
            goal.get("status", "draft"),
            goal.get("priority", "medium"),
            goal.get("owner", ""),
            json.dumps(goal.get("kpis", [])),
            json.dumps(goal.get("objectives", [])),
            goal.get("deadline"),
            json.dumps(goal.get("tags", [])),
            json.dumps(goal.get("metadata", {})),
            goal.get("created_at", datetime.utcnow()),
            goal.get("updated_at", datetime.utcnow()),
        )

    async def get(self, goal_id: str, tenant_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, tenant_id, name, description, status, priority, owner,
                   kpis, objectives, deadline, tags, metadata, created_at, updated_at
            FROM goals WHERE id = $1 AND tenant_id = $2
            """,
            goal_id,
            tenant_id,
        )
        return _row_to_dict(row, {"kpis", "objectives", "tags", "metadata"}) if row else None

    async def update(self, goal_id: str, tenant_id: str, updates: dict[str, Any]) -> None:
        self._require_db()
        set_clauses = []
        params = [goal_id, tenant_id]

        for key, value in updates.items():
            if key in ("id", "tenant_id", "created_at"):
                continue
            params.append(json.dumps(value) if isinstance(value, (list, dict)) else value)
            set_clauses.append(f"{key} = ${len(params)}" + ("::jsonb" if isinstance(value, (list, dict)) else ""))

        if not set_clauses:
            return

        params.append(datetime.utcnow())
        set_clauses.append(f"updated_at = ${len(params)}")

        query = f"""
            UPDATE goals
            SET {', '.join(set_clauses)}
            WHERE id = $1 AND tenant_id = $2
        """
        await DatabaseConnection.execute(query, *params)

    async def list_goals(
        self, tenant_id: str, status: str | None = None, owner: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        self._require_db()
        clauses = ["tenant_id = $1"]
        params = [tenant_id]

        if status:
            params.append(status)
            clauses.append(f"status = ${len(params)}")
        if owner:
            params.append(owner)
            clauses.append(f"owner = ${len(params)}")

        where = f"WHERE {' AND '.join(clauses)}"
        params.append(limit)

        rows = await DatabaseConnection.fetch(
            f"""
            SELECT id, tenant_id, name, description, status, priority, owner,
                   kpis, objectives, deadline, tags, metadata, created_at, updated_at
            FROM goals
            {where}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [_row_to_dict(row, {"kpis", "objectives", "tags", "metadata"}) for row in rows]
