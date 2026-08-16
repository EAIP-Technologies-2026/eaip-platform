"""B01 persistence foundation repositories.

Typed, tenant-scoped adapters over the existing PostgreSQL schema (created by
migration ``001_initial_schema``).  All classes reuse the shared
:class:`~eaip.infrastructure.db.connection.DatabaseConnection` pool — no second
connection abstraction is introduced.

Tenant isolation: every read is scoped to the ``tenant_id`` column added by
migration ``003_persistence_foundation``; a caller can never observe another
tenant's rows.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.logging.context import get_logger

log = get_logger("eaip.infrastructure.persistence")


class PersistenceError(Exception):
    """Base error for persistence repository operations."""


class _TenantRepository:
    """Shared helpers for tenant-scoped repositories."""

    @staticmethod
    def _require_db() -> None:
        if DatabaseConnection.get_pool() is None:
            raise PersistenceError(
                "Persistence repositories require an initialized DatabaseConnection pool."
            )


class AgentRunRepository(_TenantRepository):
    """Tenant-scoped durable storage for agent run state (``agent_runs``)."""

    async def create(
        self,
        run_id: str,
        *,
        agent_id: str,
        tenant_id: str,
        status: str = "pending",
        goal_text: str = "",
        goal_metadata: dict[str, Any] | None = None,
    ) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            INSERT INTO agent_runs
                (id, agent_id, tenant_id, status, goal_text, goal_metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            ON CONFLICT (id) DO NOTHING
            """,
            run_id,
            agent_id,
            tenant_id,
            status,
            goal_text,
            json.dumps(goal_metadata or {}),
        )

    async def get(self, run_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, agent_id, tenant_id, status, goal_text, goal_metadata,
                   result, error, duration_ms, created_at, completed_at
            FROM agent_runs WHERE id = $1
            """,
            run_id,
        )
        return _row_to_dict(row, {"goal_metadata"}) if row else None

    async def get_for_tenant(self, run_id: str, tenant_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, agent_id, tenant_id, status, goal_text, goal_metadata,
                   result, error, duration_ms, created_at, completed_at
            FROM agent_runs WHERE id = $1 AND tenant_id = $2
            """,
            run_id,
            tenant_id,
        )
        return _row_to_dict(row, {"goal_metadata"}) if row else None

    async def update_status(
        self,
        run_id: str,
        status: str,
        *,
        result: str | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        self._require_db()
        completed_at = "CASE WHEN $3 IN ('completed','failed','cancelled') THEN NOW() END"
        await DatabaseConnection.execute(
            f"""
            UPDATE agent_runs
            SET status = $2,
                result = COALESCE($4, result),
                error = $5,
                duration_ms = COALESCE($6, duration_ms),
                completed_at = {completed_at}
            WHERE id = $1
            """,
            run_id,
            status,
            status,
            result,
            error,
            duration_ms,
        )

    async def list_by_tenant(self, tenant_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        self._require_db()
        rows = await DatabaseConnection.fetch(
            """
            SELECT id, agent_id, tenant_id, status, goal_text, goal_metadata,
                   result, error, duration_ms, created_at, completed_at
            FROM agent_runs
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            tenant_id,
            limit,
        )
        return [_row_to_dict(row, {"goal_metadata"}) for row in rows]

    async def count(self, *, tenant_id: str | None = None) -> int:
        self._require_db()
        if tenant_id is None:
            return await DatabaseConnection.fetchval("SELECT COUNT(*) FROM agent_runs")
        return await DatabaseConnection.fetchval(
            "SELECT COUNT(*) FROM agent_runs WHERE tenant_id = $1", tenant_id
        )


class WorkflowRunRepository(_TenantRepository):
    """Tenant-scoped durable storage for workflow run/state (``workflow_runs``)."""

    async def create(
        self,
        run_id: str,
        *,
        workflow_id: str,
        tenant_id: str,
        status: str = "pending",
        state: str = "pending",
        context: dict[str, Any] | None = None,
    ) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            INSERT INTO workflow_runs
                (id, workflow_id, tenant_id, status, state_machine_state, context)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            ON CONFLICT (id) DO NOTHING
            """,
            run_id,
            workflow_id,
            tenant_id,
            status,
            state,
            json.dumps(context or {}),
        )

    async def get(self, run_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, workflow_id, tenant_id, status, state_machine_state,
                   context, result, error, created_at, completed_at
            FROM workflow_runs WHERE id = $1
            """,
            run_id,
        )
        return _row_to_dict(row, {"context"}) if row else None

    async def get_for_tenant(self, run_id: str, tenant_id: str) -> dict[str, Any] | None:
        self._require_db()
        row = await DatabaseConnection.fetchrow(
            """
            SELECT id, workflow_id, tenant_id, status, state_machine_state,
                   context, result, error, created_at, completed_at
            FROM workflow_runs WHERE id = $1 AND tenant_id = $2
            """,
            run_id,
            tenant_id,
        )
        return _row_to_dict(row, {"context"}) if row else None

    async def update_state(
        self,
        run_id: str,
        state: str,
        *,
        status: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._require_db()
        await DatabaseConnection.execute(
            """
            UPDATE workflow_runs
            SET state_machine_state = $2,
                status = COALESCE($3, status),
                context = COALESCE($4::jsonb, context)
            WHERE id = $1
            """,
            run_id,
            state,
            status,
            json.dumps(context) if context is not None else None,
        )

    async def list_by_tenant(self, tenant_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        self._require_db()
        rows = await DatabaseConnection.fetch(
            """
            SELECT id, workflow_id, tenant_id, status, state_machine_state,
                   context, result, error, created_at, completed_at
            FROM workflow_runs
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            tenant_id,
            limit,
        )
        return [_row_to_dict(row, {"context"}) for row in rows]

    async def count(self, *, tenant_id: str | None = None) -> int:
        self._require_db()
        if tenant_id is None:
            return await DatabaseConnection.fetchval("SELECT COUNT(*) FROM workflow_runs")
        return await DatabaseConnection.fetchval(
            "SELECT COUNT(*) FROM workflow_runs WHERE tenant_id = $1", tenant_id
        )


class AuditEventRepository(_TenantRepository):
    """Append-only tenant-scoped audit log (``audit_events``).

    Only INSERT and SELECT are permitted — no UPDATE, no DELETE.  This mirrors
    the append-only, immutable semantics of the audit domain.
    """

    async def append(
        self,
        *,
        event_type: str,
        action: str,
        actor_id: str,
        actor_type: str = "user",
        resource_type: str = "",
        resource_id: str | None = None,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> str:
        self._require_db()
        entry_id = f"audit-{_new_id()}"
        await DatabaseConnection.execute(
            """
            INSERT INTO audit_events
                (id, event_type, actor_id, actor_type, resource_type, resource_id,
                 action, changes, metadata, organization_id, tenant_id, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, NULL, $10, $11, $12)
            """,
            entry_id,
            event_type,
            actor_id,
            actor_type,
            resource_type,
            resource_id,
            action,
            json.dumps(changes or {}),
            json.dumps(metadata or {}),
            tenant_id,
            ip_address,
            user_agent,
        )
        return entry_id

    async def query(
        self,
        tenant_id: str | None = None,
        *,
        event_type: str | None = None,
        actor_id: str | None = None,
        action: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self._require_db()
        clauses: list[str] = []
        params: list[Any] = []
        if tenant_id is not None:
            params.append(tenant_id)
            clauses.append(f"tenant_id = ${len(params)}")
        if event_type is not None:
            params.append(event_type)
            clauses.append(f"event_type = ${len(params)}")
        if actor_id is not None:
            params.append(actor_id)
            clauses.append(f"actor_id = ${len(params)}")
        if action is not None:
            params.append(action)
            clauses.append(f"action = ${len(params)}")
        if since is not None:
            params.append(since)
            clauses.append(f"created_at >= ${len(params)}")
        if until is not None:
            params.append(until)
            clauses.append(f"created_at <= ${len(params)}")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        rows = await DatabaseConnection.fetch(
            f"""
            SELECT id, event_type, actor_id, actor_type, resource_type, resource_id,
                   action, changes, metadata, tenant_id, ip_address, user_agent, created_at
            FROM audit_events
            {where}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [_row_to_dict(row, {"changes", "metadata"}) for row in rows]

    async def count(self, *, tenant_id: str | None = None) -> int:
        self._require_db()
        if tenant_id is None:
            return await DatabaseConnection.fetchval("SELECT COUNT(*) FROM audit_events")
        return await DatabaseConnection.fetchval(
            "SELECT COUNT(*) FROM audit_events WHERE tenant_id = $1", tenant_id
        )


def _row_to_dict(row: Any, json_columns: set[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in row.keys():
        value = row[key]
        if key in json_columns and isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
        result[key] = value
    return result


def _new_id() -> str:
    from uuid import uuid4

    return uuid4().hex


from .automation import AutomationRepository
from .collaboration import CollaborationRepository
from .decisions import DecisionRepository
from .goals import GoalRepository
from .pulse import PulseRepository
from .recommendations import RecommendationRepository
from .skills import SkillRepository
from .templates import AgentTemplateRepository
from .workflows import WorkflowRepository

__all__ = [
    "AgentRunRepository",
    "AgentTemplateRepository",
    "AuditEventRepository",
    "AutomationRepository",
    "CollaborationRepository",
    "DecisionRepository",
    "GoalRepository",
    "PersistenceError",
    "PulseRepository",
    "RecommendationRepository",
    "SkillRepository",
    "WorkflowRepository",
    "WorkflowRunRepository",
]
