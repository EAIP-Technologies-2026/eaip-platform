"""Persistence repository for Skills."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence import _row_to_dict, _TenantRepository


class SkillRepository(_TenantRepository):
    """Tenant-scoped durable storage for skills."""

    async def create(self, skill: dict[str, Any]) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            INSERT INTO skills
                (id, tenant_id, name, description, version, parameters, 
                 entry_point, capabilities, metadata, created_by, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8::jsonb, $9::jsonb, $10, $11, $12)
            ON CONFLICT (id, tenant_id) DO NOTHING
            """,
            skill["id"],
            skill.get("tenant_id", "default"),
            skill["name"],
            skill.get("description", ""),
            skill.get("version", "0.1.0"),
            json.dumps(skill.get("parameters", {})),
            skill.get("entry_point", ""),
            json.dumps(skill.get("capabilities", [])),
            json.dumps(skill.get("metadata", {})),
            skill.get("created_by", ""),
            skill.get("created_at", datetime.utcnow()),
            skill.get("updated_at", datetime.utcnow()),
        )

    async def get(self, skill_id: str, tenant_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, tenant_id, name, description, version, parameters, 
                   entry_point, capabilities, metadata, created_by, created_at, updated_at
            FROM skills WHERE id = $1 AND tenant_id = $2
            """,
            skill_id,
            tenant_id,
        )
        return _row_to_dict(row, {"parameters", "capabilities", "metadata"}) if row else None

    async def update(self, skill_id: str, tenant_id: str, updates: dict[str, Any]) -> None:
        self._require_db()
        set_clauses = []
        params = [skill_id, tenant_id]

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
            UPDATE skills
            SET {', '.join(set_clauses)}
            WHERE id = $1 AND tenant_id = $2
        """
        await DatabaseConnection.execute(query, *params)

    async def delete(self, skill_id: str, tenant_id: str) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            UPDATE skills
            SET deleted_at = NOW()
            WHERE id = $1 AND tenant_id = $2
            """,
            skill_id,
            tenant_id,
        )

    async def list_skills(self, tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
        self._require_db()
        rows = await DatabaseConnection.fetch(
            """
            SELECT id, tenant_id, name, description, version, parameters, 
                   entry_point, capabilities, metadata, created_by, created_at, updated_at
            FROM skills
            WHERE tenant_id = $1 AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT $2
            """,
            tenant_id,
            limit,
        )
        return [_row_to_dict(row, {"parameters", "capabilities", "metadata"}) for row in rows]
