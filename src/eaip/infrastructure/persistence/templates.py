"""Persistence repository for Agent Templates."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence import _row_to_dict, _TenantRepository


class AgentTemplateRepository(_TenantRepository):
    """Tenant-scoped durable storage for agent templates."""

    async def create(self, template: dict[str, Any]) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            INSERT INTO agent_templates
                (id, tenant_id, name, description, version, llm_config, 
                 tools, system_prompt_template, metadata, created_by, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9::jsonb, $10, $11, $12)
            ON CONFLICT (id, tenant_id) DO NOTHING
            """,
            template["id"],
            template.get("tenant_id", "default"),
            template["name"],
            template.get("description", ""),
            template.get("version", "0.1.0"),
            json.dumps(template.get("llm_config", {})),
            json.dumps(template.get("tools", [])),
            template.get("system_prompt_template", ""),
            json.dumps(template.get("metadata", {})),
            template.get("created_by", ""),
            template.get("created_at", datetime.utcnow()),
            template.get("updated_at", datetime.utcnow()),
        )

    async def get(self, template_id: str, tenant_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, tenant_id, name, description, version, llm_config, 
                   tools, system_prompt_template, metadata, created_by, created_at, updated_at
            FROM agent_templates WHERE id = $1 AND tenant_id = $2
            """,
            template_id,
            tenant_id,
        )
        return _row_to_dict(row, {"llm_config", "tools", "metadata"}) if row else None

    async def update(self, template_id: str, tenant_id: str, updates: dict[str, Any]) -> None:
        self._require_db()
        set_clauses = []
        params = [template_id, tenant_id]

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
            UPDATE agent_templates
            SET {', '.join(set_clauses)}
            WHERE id = $1 AND tenant_id = $2
        """
        await DatabaseConnection.execute(query, *params)

    async def delete(self, template_id: str, tenant_id: str) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            UPDATE agent_templates
            SET deleted_at = NOW()
            WHERE id = $1 AND tenant_id = $2
            """,
            template_id,
            tenant_id,
        )

    async def list_templates(self, tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
        self._require_db()
        rows = await DatabaseConnection.fetch(
            """
            SELECT id, tenant_id, name, description, version, llm_config, 
                   tools, system_prompt_template, metadata, created_by, created_at, updated_at
            FROM agent_templates
            WHERE tenant_id = $1 AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT $2
            """,
            tenant_id,
            limit,
        )
        return [_row_to_dict(row, {"llm_config", "tools", "metadata"}) for row in rows]
