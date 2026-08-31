"""Persistence repository for Workflow Definitions."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence import _row_to_dict, _TenantRepository


class WorkflowRepository(_TenantRepository):
    """Tenant-scoped durable storage for workflow definitions (``workflows``).
    Note: m001 defined 'organization_id' which maps to 'tenant_id'.
    """

    async def create(self, workflow: dict[str, Any]) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            INSERT INTO workflows
                (id, name, description, version, steps, edges, parallel_groups, entry_point,
                 triggers, timeout_config, metadata, status, organization_id, created_by,
                 created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb, $8, $9::jsonb, $10::jsonb,
                    $11::jsonb, $12, $13, $14, $15, $16)
            ON CONFLICT (id) DO NOTHING
            """,
            workflow["id"],
            workflow["name"],
            workflow.get("description", ""),
            workflow.get("version", "0.1.0"),
            json.dumps(workflow.get("steps", [])),
            json.dumps(workflow.get("edges", [])),
            json.dumps(workflow.get("parallel_groups", [])),
            workflow.get("entry_point", ""),
            json.dumps(workflow.get("triggers", [])),
            json.dumps(workflow.get("timeout_config")) if workflow.get("timeout_config") else None,
            json.dumps(workflow.get("metadata", {})),
            workflow.get("status", "draft"),
            workflow.get("tenant_id"), # Maps to organization_id
            workflow.get("created_by"),
            workflow.get("created_at", datetime.utcnow()),
            workflow.get("updated_at", datetime.utcnow()),
        )

    async def get(self, workflow_id: str, tenant_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, name, description, version, steps, edges, parallel_groups, entry_point,
                   triggers, timeout_config, metadata, status, organization_id as tenant_id, created_by,
                   created_at, updated_at, published_at
            FROM workflows 
            WHERE id = $1 AND (organization_id = $2 OR organization_id IS NULL)
            """,
            workflow_id,
            tenant_id,
        )
        return _row_to_dict(row, {"steps", "edges", "parallel_groups", "triggers", "timeout_config", "metadata"}) if row else None

    async def update(self, workflow_id: str, tenant_id: str, updates: dict[str, Any]) -> None:
        self._require_db()
        set_clauses = []
        params = [workflow_id, tenant_id]

        for key, value in updates.items():
            if key in ("id", "tenant_id", "created_at", "organization_id"):
                continue
            params.append(json.dumps(value) if isinstance(value, (list, dict)) else value)
            set_clauses.append(f"{key} = ${len(params)}" + ("::jsonb" if isinstance(value, (list, dict)) else ""))

        if not set_clauses:
            return

        params.append(datetime.utcnow())
        set_clauses.append(f"updated_at = ${len(params)}")

        query = f"""
            UPDATE workflows
            SET {', '.join(set_clauses)}
            WHERE id = $1 AND (organization_id = $2 OR organization_id IS NULL)
        """
        await DatabaseConnection.execute(query, *params)

    async def list_workflows(
        self, tenant_id: str, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        self._require_db()
        clauses = ["(organization_id = $1 OR organization_id IS NULL)", "deleted_at IS NULL"]
        params: list[Any] = [tenant_id]

        if status:
            params.append(status)
            clauses.append(f"status = ${len(params)}")

        where = f"WHERE {' AND '.join(clauses)}"
        params.append(limit)

        rows = await DatabaseConnection.fetch(
            f"""
            SELECT id, name, description, version, steps, edges, parallel_groups, entry_point,
                   triggers, timeout_config, metadata, status, organization_id as tenant_id, created_by,
                   created_at, updated_at, published_at
            FROM workflows
            {where}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [_row_to_dict(row, {"steps", "edges", "parallel_groups", "triggers", "timeout_config", "metadata"}) for row in rows]
