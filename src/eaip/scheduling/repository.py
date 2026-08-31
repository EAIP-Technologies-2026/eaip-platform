from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.logging.context import get_logger
from eaip.scheduling.exceptions import ScheduleNotFoundError
from eaip.scheduling.models import (
    ExecutionWindow,
    RetryPolicy,
    ScheduleDefinition,
    ScheduleExecution,
    ScheduleKind,
    ScheduleStatus,
    ScheduleTargetType,
    ScheduleTrigger,
)

log = get_logger("eaip.scheduling.repository")


def _schedule_key(tenant_id: str, schedule_id: str) -> str:
    return f"{tenant_id}:{schedule_id}"


def _is_pool_available() -> bool:
    try:
        return DatabaseConnection.get_pool() is not None
    except Exception:
        return False


def _def_to_row(defn: ScheduleDefinition) -> dict[str, Any]:
    return {
        "id": defn.id,
        "tenant_id": defn.tenant_id,
        "name": defn.name,
        "description": defn.description,
        "target_type": defn.target_type.value,
        "target_id": defn.target_id,
        "trigger_config": json.dumps(defn.trigger.model_dump(mode="json")),
        "window_config": json.dumps(
            defn.execution_window.model_dump(mode="json") if defn.execution_window else None
        ),
        "priority": defn.priority,
        "dependencies": list(defn.dependencies),
        "retry_policy": json.dumps(defn.retry_policy.model_dump(mode="json")),
        "status": defn.status.value,
        "created_by": defn.created_by,
        "created_at": defn.created_at,
        "updated_at": defn.updated_at,
        "next_run_at": defn.next_run_at,
        "last_run_at": defn.last_run_at,
        "metadata": json.dumps(defn.metadata),
    }


def _row_to_def(row: Any) -> ScheduleDefinition:
    trigger_raw = row["trigger_config"]
    if isinstance(trigger_raw, str):
        trigger_raw = json.loads(trigger_raw)
    window_raw = row["window_config"]
    if isinstance(window_raw, str):
        window_raw = json.loads(window_raw)
    retry_raw = row["retry_policy"]
    if isinstance(retry_raw, str):
        retry_raw = json.loads(retry_raw)
    metadata_raw = row["metadata"]
    if isinstance(metadata_raw, str):
        try:
            metadata_raw = json.loads(metadata_raw)
        except (json.JSONDecodeError, TypeError):
            metadata_raw = {}
    elif metadata_raw is None:
        metadata_raw = {}

    deps = row["dependencies"] or []
    if isinstance(deps, str):
        try:
            deps = json.loads(deps)
        except (json.JSONDecodeError, TypeError):
            deps = []

    trigger = ScheduleTrigger.model_validate(trigger_raw) if trigger_raw else ScheduleTrigger(kind=ScheduleKind.ONE_TIME)
    window = ExecutionWindow.model_validate(window_raw) if window_raw else None
    retry = RetryPolicy.model_validate(retry_raw) if retry_raw else RetryPolicy()

    return ScheduleDefinition(
        id=row["id"],
        tenant_id=row["tenant_id"],
        name=row["name"],
        description=row["description"] or "",
        target_type=ScheduleTargetType(row["target_type"]),
        target_id=row["target_id"],
        trigger=trigger,
        execution_window=window,
        priority=int(row["priority"] or 1),
        dependencies=tuple(deps),
        retry_policy=retry,
        status=ScheduleStatus(row["status"]),
        created_by=row["created_by"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        next_run_at=row["next_run_at"],
        last_run_at=row["last_run_at"],
        metadata=metadata_raw if isinstance(metadata_raw, dict) else {},
    )


def _row_to_exec(row: Any) -> ScheduleExecution:
    return ScheduleExecution(
        id=row["id"],
        schedule_id=row["schedule_id"],
        tenant_id=row["tenant_id"],
        status=row["status"],
        attempt=int(row["attempt"] or 1),
        scheduled_at=row["scheduled_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        result=row["result"] or "",
        error=row["error"],
    )


class ScheduleRepository:
    def __init__(self) -> None:
        self._store: dict[str, ScheduleDefinition] = {}
        self._exec_store: dict[str, ScheduleDefinition] = {}  # compatibility alias
        self._in_memory: bool = False
        self._log = get_logger("eaip.scheduling.repository.schedules")

    @property
    def _in_memory_flag(self) -> bool:
        return self._in_memory or not _is_pool_available()

    @property
    def _pool(self) -> Any | None:
        try:
            return DatabaseConnection.get_pool()
        except Exception:
            return None

    def _key(self, tenant_id: str, schedule_id: str) -> str:
        return _schedule_key(tenant_id, schedule_id)

    async def create(self, definition: ScheduleDefinition) -> ScheduleDefinition:
        if not _is_pool_available():
            self._in_memory = True
            key = self._key(definition.tenant_id, definition.id)
            self._store[key] = definition
            return definition
        try:
            row = _def_to_row(definition)
            await DatabaseConnection.execute(
                """
                INSERT INTO schedules
                    (id, tenant_id, name, description, target_type, target_id,
                     trigger_config, window_config, priority, dependencies, retry_policy,
                     status, created_by, created_at, updated_at, next_run_at, last_run_at, metadata)
                VALUES
                    ($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9,$10,$11::jsonb,$12,$13,$14,$15,$16,$17,$18::jsonb)
                ON CONFLICT (id, tenant_id) DO NOTHING
                """,
                row["id"],
                row["tenant_id"],
                row["name"],
                row["description"],
                row["target_type"],
                row["target_id"],
                row["trigger_config"],
                row["window_config"],
                row["priority"],
                row["dependencies"],
                row["retry_policy"],
                row["status"],
                row["created_by"],
                row["created_at"],
                row["updated_at"],
                row["next_run_at"],
                row["last_run_at"],
                row["metadata"],
            )
            return definition
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                key = self._key(definition.tenant_id, definition.id)
                self._store[key] = definition
                return definition
            raise

    async def get(self, schedule_id: str, tenant_id: str) -> ScheduleDefinition | None:
        if not _is_pool_available():
            self._in_memory = True
            return self._store.get(self._key(tenant_id, schedule_id))
        try:
            row = await DatabaseConnection.fetchrow(
                "SELECT * FROM schedules WHERE id = $1 AND tenant_id = $2",
                schedule_id,
                tenant_id,
            )
            if row is None:
                key = self._key(tenant_id, schedule_id)
                return self._store.get(key)
            return _row_to_def(row)
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                return self._store.get(self._key(tenant_id, schedule_id))
            raise

    async def list_by_tenant(
        self,
        tenant_id: str,
        status: ScheduleStatus | str | None = None,
        kind: ScheduleKind | str | None = None,
        priority: int | None = None,
        limit: int = 100,
    ) -> list[ScheduleDefinition]:
        if not _is_pool_available():
            self._in_memory = True
            results = [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:")]
            if status is not None:
                sv = status.value if isinstance(status, ScheduleStatus) else str(status)
                results = [r for r in results if r.status.value == sv]
            if kind is not None:
                kv = kind.value if isinstance(kind, ScheduleKind) else str(kind)
                results = [r for r in results if r.trigger.kind.value == kv]
            if priority is not None:
                results = [r for r in results if r.priority == priority]
            return results[:limit]
        try:
            clauses: list[str] = ["tenant_id = $1"]
            params: list[Any] = [tenant_id]
            if status is not None:
                sv = status.value if isinstance(status, ScheduleStatus) else str(status)
                params.append(sv)
                clauses.append(f"status = ${len(params)}")
            if priority is not None:
                params.append(priority)
                clauses.append(f"priority = ${len(params)}")
            where = " AND ".join(clauses)
            params.append(limit)
            rows = await DatabaseConnection.fetch(
                f"SELECT * FROM schedules WHERE {where} ORDER BY created_at DESC LIMIT ${len(params)}",
                *params,
            )
            defs = [_row_to_def(r) for r in rows]
            if kind is not None:
                kv = kind.value if isinstance(kind, ScheduleKind) else str(kind)
                defs = [d for d in defs if d.trigger.kind.value == kv]
            return defs
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                results = [v for k, v in self._store.items() if k.startswith(f"{tenant_id}:")]
                if status is not None:
                    sv = status.value if isinstance(status, ScheduleStatus) else str(status)
                    results = [r for r in results if r.status.value == sv]
                if kind is not None:
                    kv = kind.value if isinstance(kind, ScheduleKind) else str(kind)
                    results = [r for r in results if r.trigger.kind.value == kv]
                if priority is not None:
                    results = [r for r in results if r.priority == priority]
                return results[:limit]
            raise

    async def update(
        self, schedule_id: str, tenant_id: str, updates: dict[str, Any]
    ) -> ScheduleDefinition | None:
        existing = await self.get(schedule_id, tenant_id)
        if existing is None:
            return None
        merged = existing.model_dump()
        merged.update(updates)
        if "trigger" in updates and isinstance(updates["trigger"], dict):
            merged["trigger"] = updates["trigger"]
        if "execution_window" in updates and isinstance(updates["execution_window"], dict):
            merged["execution_window"] = updates["execution_window"]
        if "retry_policy" in updates and isinstance(updates["retry_policy"], dict):
            merged["retry_policy"] = updates["retry_policy"]
        updated = ScheduleDefinition.model_validate(merged)

        if not _is_pool_available():
            self._in_memory = True
            self._store[self._key(tenant_id, schedule_id)] = updated
            return updated
        try:
            row = _def_to_row(updated)
            await DatabaseConnection.execute(
                """
                UPDATE schedules SET
                    name = $3, description = $4, target_type = $5, target_id = $6,
                    trigger_config = $7::jsonb, window_config = $8::jsonb, priority = $9,
                    dependencies = $10, retry_policy = $11::jsonb, status = $12,
                    updated_at = $13, next_run_at = $14, last_run_at = $15, metadata = $16::jsonb
                WHERE id = $1 AND tenant_id = $2
                """,
                row["id"],
                row["tenant_id"],
                row["name"],
                row["description"],
                row["target_type"],
                row["target_id"],
                row["trigger_config"],
                row["window_config"],
                row["priority"],
                row["dependencies"],
                row["retry_policy"],
                row["status"],
                row["updated_at"],
                row["next_run_at"],
                row["last_run_at"],
                row["metadata"],
            )
            self._store[self._key(tenant_id, schedule_id)] = updated
            return updated
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                self._store[self._key(tenant_id, schedule_id)] = updated
                return updated
            raise

    async def delete(self, schedule_id: str, tenant_id: str) -> bool:
        existed_in_memory = self._store.pop(self._key(tenant_id, schedule_id), None) is not None
        if not _is_pool_available():
            self._in_memory = True
            return existed_in_memory
        try:
            result = await DatabaseConnection.execute(
                "DELETE FROM schedules WHERE id = $1 AND tenant_id = $2",
                schedule_id,
                tenant_id,
            )
            deleted = "DELETE 1" in str(result) if result else False
            return deleted or existed_in_memory
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                return existed_in_memory
            raise

    async def get_due(self, tenant_id: str, now: datetime) -> list[ScheduleDefinition]:
        if not _is_pool_available():
            self._in_memory = True
            return [
                v
                for k, v in self._store.items()
                if k.startswith(f"{tenant_id}:")
                and v.status == ScheduleStatus.ACTIVE
                and v.next_run_at is not None
                and v.next_run_at <= now
            ]
        try:
            rows = await DatabaseConnection.fetch(
                "SELECT * FROM schedules WHERE tenant_id = $1 AND status = 'active' AND next_run_at IS NOT NULL AND next_run_at <= $2",
                tenant_id,
                now,
            )
            return [_row_to_def(r) for r in rows]
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                return [
                    v
                    for k, v in self._store.items()
                    if k.startswith(f"{tenant_id}:")
                    and v.status == ScheduleStatus.ACTIVE
                    and v.next_run_at is not None
                    and v.next_run_at <= now
                ]
            raise

    async def get_all_due(self, now: datetime) -> list[ScheduleDefinition]:
        if not _is_pool_available():
            self._in_memory = True
            return [
                v
                for v in self._store.values()
                if v.status == ScheduleStatus.ACTIVE
                and v.next_run_at is not None
                and v.next_run_at <= now
            ]
        try:
            rows = await DatabaseConnection.fetch(
                "SELECT * FROM schedules WHERE status = 'active' AND next_run_at IS NOT NULL AND next_run_at <= $1",
                now,
            )
            return [_row_to_def(r) for r in rows]
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                return [
                    v
                    for v in self._store.values()
                    if v.status == ScheduleStatus.ACTIVE
                    and v.next_run_at is not None
                    and v.next_run_at <= now
                ]
            raise


class ScheduleExecutionRepository:
    def __init__(self) -> None:
        self._store: dict[str, ScheduleExecution] = {}
        self._exec_store: dict[str, ScheduleExecution] = self._store
        self._in_memory: bool = False

    @property
    def _pool(self) -> Any | None:
        try:
            return DatabaseConnection.get_pool()
        except Exception:
            return None

    async def create(self, execution: ScheduleExecution) -> ScheduleExecution:
        if not _is_pool_available():
            self._in_memory = True
            key = f"{execution.tenant_id}:{execution.schedule_id}:{execution.id}"
            self._store[key] = execution
            return execution
        try:
            await DatabaseConnection.execute(
                """
                INSERT INTO schedule_executions
                    (id, schedule_id, tenant_id, status, attempt, scheduled_at, started_at, completed_at, result, error)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                ON CONFLICT (id) DO NOTHING
                """,
                execution.id,
                execution.schedule_id,
                execution.tenant_id,
                execution.status,
                execution.attempt,
                execution.scheduled_at,
                execution.started_at,
                execution.completed_at,
                execution.result,
                execution.error,
            )
            key = f"{execution.tenant_id}:{execution.schedule_id}:{execution.id}"
            self._store[key] = execution
            return execution
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                key = f"{execution.tenant_id}:{execution.schedule_id}:{execution.id}"
                self._store[key] = execution
                return execution
            raise

    async def list_by_schedule(
        self, schedule_id: str, tenant_id: str, limit: int = 50
    ) -> list[ScheduleExecution]:
        if not _is_pool_available():
            self._in_memory = True
            results = [
                v for v in self._store.values() if v.schedule_id == schedule_id and v.tenant_id == tenant_id
            ]
            results.sort(key=lambda e: e.scheduled_at, reverse=True)
            return results[:limit]
        try:
            rows = await DatabaseConnection.fetch(
                "SELECT * FROM schedule_executions WHERE schedule_id = $1 AND tenant_id = $2 ORDER BY scheduled_at DESC LIMIT $3",
                schedule_id,
                tenant_id,
                limit,
            )
            if not rows:
                results = [
                    v for v in self._store.values() if v.schedule_id == schedule_id and v.tenant_id == tenant_id
                ]
                results.sort(key=lambda e: e.scheduled_at, reverse=True)
                return results[:limit]
            return [_row_to_exec(r) for r in rows]
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                results = [
                    v for v in self._store.values() if v.schedule_id == schedule_id and v.tenant_id == tenant_id
                ]
                results.sort(key=lambda e: e.scheduled_at, reverse=True)
                return results[:limit]
            raise

    async def list_by_tenant(self, tenant_id: str, limit: int = 50) -> list[ScheduleExecution]:
        if not _is_pool_available():
            self._in_memory = True
            results = [v for v in self._store.values() if v.tenant_id == tenant_id]
            results.sort(key=lambda e: e.scheduled_at, reverse=True)
            return results[:limit]
        try:
            rows = await DatabaseConnection.fetch(
                "SELECT * FROM schedule_executions WHERE tenant_id = $1 ORDER BY scheduled_at DESC LIMIT $2",
                tenant_id,
                limit,
            )
            if not rows:
                results = [v for v in self._store.values() if v.tenant_id == tenant_id]
                results.sort(key=lambda e: e.scheduled_at, reverse=True)
                return results[:limit]
            return [_row_to_exec(r) for r in rows]
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._in_memory = True
                results = [v for v in self._store.values() if v.tenant_id == tenant_id]
                results.sort(key=lambda e: e.scheduled_at, reverse=True)
                return results[:limit]
            raise


__all__ = ["ScheduleExecutionRepository", "ScheduleRepository"]
