"""Persistence repository for B06 Automation Rules."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence import _row_to_dict, _TenantRepository


class AutomationRepository(_TenantRepository):
    """Tenant-scoped durable storage for automation rules (``automation_rules``)."""

    async def create(self, rule: dict[str, Any]) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            INSERT INTO automation_rules
                (id, tenant_id, name, description, status, trigger_config, action_config,
                 conditions, metadata, created_by, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb, $10, $11, $12)
            ON CONFLICT (id, tenant_id) DO NOTHING
            """,
            rule["id"],
            rule.get("tenant_id", "default"),
            rule["name"],
            rule.get("description", ""),
            rule.get("status", "active"),
            json.dumps(rule.get("trigger_config", {})),
            json.dumps(rule.get("action_config", {})),
            json.dumps(rule.get("conditions", [])),
            json.dumps(rule.get("metadata", {})),
            rule.get("created_by", ""),
            rule.get("created_at", datetime.utcnow()),
            rule.get("updated_at", datetime.utcnow()),
        )

    async def get(self, rule_id: str, tenant_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, tenant_id, name, description, status, trigger_config, action_config,
                   conditions, metadata, created_by, created_at, updated_at
            FROM automation_rules WHERE id = $1 AND tenant_id = $2
            """,
            rule_id,
            tenant_id,
        )
        return _row_to_dict(row, {"trigger_config", "action_config", "conditions", "metadata"}) if row else None

    async def update(self, rule_id: str, tenant_id: str, updates: dict[str, Any]) -> None:
        self._require_db()
        set_clauses = []
        params = [rule_id, tenant_id]

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
            UPDATE automation_rules
            SET {', '.join(set_clauses)}
            WHERE id = $1 AND tenant_id = $2
        """
        await DatabaseConnection.execute(query, *params)

    async def delete(self, rule_id: str, tenant_id: str) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            UPDATE automation_rules
            SET deleted_at = NOW()
            WHERE id = $1 AND tenant_id = $2
            """,
            rule_id,
            tenant_id,
        )

    async def list_rules(
        self, tenant_id: str, trigger_type: str | None = None, enabled: bool | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        self._require_db()
        clauses = ["tenant_id = $1", "deleted_at IS NULL"]
        params: list[Any] = [tenant_id]

        if trigger_type:
            params.append(trigger_type)
            clauses.append(f"trigger_config->>'type' = ${len(params)}")

        if enabled is not None:
            status = "active" if enabled else "disabled"
            params.append(status)
            clauses.append(f"status = ${len(params)}")

        where = f"WHERE {' AND '.join(clauses)}"
        params.append(limit)

        rows = await DatabaseConnection.fetch(
            f"""
            SELECT id, tenant_id, name, description, status, trigger_config, action_config,
                   conditions, metadata, created_by, created_at, updated_at
            FROM automation_rules
            {where}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [_row_to_dict(row, {"trigger_config", "action_config", "conditions", "metadata"}) for row in rows]
