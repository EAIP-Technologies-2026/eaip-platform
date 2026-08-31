from __future__ import annotations

from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.logging.context import get_logger
from eaip.workforce.models import AssignmentStatus, WorkerAssignment, WorkerDefinition, WorkerType

log = get_logger("eaip.workforce.persistence")


def _is_pool_available() -> bool:
    try:
        return DatabaseConnection.get_pool() is not None
    except Exception:
        return False


def _row_to_worker(row: Any) -> WorkerDefinition:
    raw_tags = row["tags"] if "tags" in row else row.get("tags", [])
    if raw_tags is None:
        raw_tags = []
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags] if raw_tags else []
    tags = tuple(str(t) for t in raw_tags)
    wt_raw = row["worker_type"] if "worker_type" in row else row.get("worker_type", "agent")
    try:
        wt = WorkerType(str(wt_raw))
    except Exception:
        wt = WorkerType.AGENT
    return WorkerDefinition(
        id=str(row["id"] if "id" in row else row.get("id", "")),
        name=str(row["name"] if "name" in row else row.get("name", "")),
        worker_type=wt,
        agent_id=str(row["agent_id"] if "agent_id" in row else row.get("agent_id", "")),
        workflow_id=str(row["workflow_id"] if "workflow_id" in row else row.get("workflow_id", "")),
        description=str(row["description"] if "description" in row else row.get("description", "")),
        tags=tags,
        max_concurrent_runs=int(row["max_concurrent_runs"] if "max_concurrent_runs" in row else row.get("max_concurrent_runs", 1) or 1),
    )


def _row_to_assignment(row: Any) -> WorkerAssignment:
    status_raw = row["status"] if "status" in row else row.get("status", "pending")
    try:
        status = AssignmentStatus(str(status_raw))
    except Exception:
        status = AssignmentStatus.PENDING
    return WorkerAssignment(
        id=str(row["id"] if "id" in row else row.get("id", "")),
        worker_id=str(row["worker_id"] if "worker_id" in row else row.get("worker_id", "")),
        task_description=str(row["task_description"] if "task_description" in row else row.get("task_description", "")),
        status=status,
        assigned_at=row["assigned_at"] if "assigned_at" in row else row.get("assigned_at"),
        completed_at=row["completed_at"] if "completed_at" in row else row.get("completed_at"),
        result=str(row["result"] if "result" in row else row.get("result", "") or ""),
        error=row["error"] if "error" in row else row.get("error"),
        run_id=str(row["run_id"] if "run_id" in row else row.get("run_id", "") or ""),
        priority=int(row["priority"] if "priority" in row else row.get("priority", 0) or 0),
    )


class WorkforceRepository:
    def __init__(self) -> None:
        self._workers: dict[str, WorkerDefinition] = {}
        self._assignments: dict[str, WorkerAssignment] = {}
        self._log = get_logger("eaip.workforce.persistence.repository")

    def _worker_key(self, tenant_id: str, worker_id: str) -> str:
        return f"{tenant_id}:{worker_id}"

    def _assignment_key(self, tenant_id: str, assignment_id: str) -> str:
        return f"{tenant_id}:{assignment_id}"

    async def save_worker(self, worker: WorkerDefinition, tenant_id: str) -> WorkerDefinition:
        key = self._worker_key(tenant_id, worker.id)
        if not _is_pool_available():
            self._workers[key] = worker
            return worker
        try:
            await DatabaseConnection.execute(
                """
                INSERT INTO workforce_workers
                    (id, tenant_id, worker_type, agent_id, workflow_id, name, description, tags, max_concurrent_runs, status)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                ON CONFLICT (id, tenant_id) DO UPDATE SET
                    worker_type = EXCLUDED.worker_type,
                    agent_id = EXCLUDED.agent_id,
                    workflow_id = EXCLUDED.workflow_id,
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    tags = EXCLUDED.tags,
                    max_concurrent_runs = EXCLUDED.max_concurrent_runs,
                    status = EXCLUDED.status
                """,
                worker.id,
                tenant_id,
                worker.worker_type.value,
                worker.agent_id,
                worker.workflow_id,
                worker.name,
                worker.description,
                list(worker.tags),
                worker.max_concurrent_runs,
                "active",
            )
            self._workers[key] = worker
            return worker
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._workers[key] = worker
                return worker
            self._log.warning("workforce.save_worker.fallback", error=repr(exc), worker_id=worker.id)
            self._workers[key] = worker
            return worker

    async def get_worker(self, worker_id: str, tenant_id: str) -> WorkerDefinition | None:
        key = self._worker_key(tenant_id, worker_id)
        if not _is_pool_available():
            return self._workers.get(key)
        try:
            row = await DatabaseConnection.fetchrow(
                "SELECT * FROM workforce_workers WHERE id = $1 AND tenant_id = $2",
                worker_id,
                tenant_id,
            )
            if row is None:
                return self._workers.get(key)
            definition = _row_to_worker(row)
            self._workers[key] = definition
            return definition
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                return self._workers.get(key)
            self._log.warning("workforce.get_worker.fallback", error=repr(exc), worker_id=worker_id)
            return self._workers.get(key)

    async def list_workers(self, tenant_id: str) -> list[WorkerDefinition]:
        if not _is_pool_available():
            return [v for k, v in self._workers.items() if k.startswith(f"{tenant_id}:")]
        try:
            rows = await DatabaseConnection.fetch(
                "SELECT * FROM workforce_workers WHERE tenant_id = $1 ORDER BY created_at DESC",
                tenant_id,
            )
            if not rows:
                cached = [v for k, v in self._workers.items() if k.startswith(f"{tenant_id}:")]
                if cached:
                    return cached
                return []
            results: list[WorkerDefinition] = []
            for row in rows:
                definition = _row_to_worker(row)
                key = self._worker_key(tenant_id, definition.id)
                self._workers[key] = definition
                results.append(definition)
            return results
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                return [v for k, v in self._workers.items() if k.startswith(f"{tenant_id}:")]
            self._log.warning("workforce.list_workers.fallback", error=repr(exc))
            return [v for k, v in self._workers.items() if k.startswith(f"{tenant_id}:")]

    async def save_assignment(self, assignment: WorkerAssignment, tenant_id: str) -> WorkerAssignment:
        key = self._assignment_key(tenant_id, assignment.id)
        if not _is_pool_available():
            self._assignments[key] = assignment
            return assignment
        try:
            await DatabaseConnection.execute(
                """
                INSERT INTO workforce_assignments
                    (id, tenant_id, worker_id, task_description, status, assigned_at, completed_at, result, error, run_id, priority)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                ON CONFLICT (id, tenant_id) DO UPDATE SET
                    worker_id = EXCLUDED.worker_id,
                    task_description = EXCLUDED.task_description,
                    status = EXCLUDED.status,
                    assigned_at = EXCLUDED.assigned_at,
                    completed_at = EXCLUDED.completed_at,
                    result = EXCLUDED.result,
                    error = EXCLUDED.error,
                    run_id = EXCLUDED.run_id,
                    priority = EXCLUDED.priority
                """,
                assignment.id,
                tenant_id,
                assignment.worker_id,
                assignment.task_description,
                assignment.status.value,
                assignment.assigned_at,
                assignment.completed_at,
                assignment.result,
                assignment.error,
                assignment.run_id,
                assignment.priority,
            )
            self._assignments[key] = assignment
            return assignment
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                self._assignments[key] = assignment
                return assignment
            self._log.warning("workforce.save_assignment.fallback", error=repr(exc), assignment_id=assignment.id)
            self._assignments[key] = assignment
            return assignment

    async def list_assignments(
        self,
        tenant_id: str,
        worker_id: str | None = None,
        status: AssignmentStatus | str | None = None,
    ) -> list[WorkerAssignment]:
        if not _is_pool_available():
            results = [v for k, v in self._assignments.items() if k.startswith(f"{tenant_id}:")]
            if worker_id is not None:
                results = [a for a in results if a.worker_id == worker_id]
            if status is not None:
                sv = status.value if isinstance(status, AssignmentStatus) else str(status)
                results = [a for a in results if a.status.value == sv]
            return results
        try:
            clauses: list[str] = ["tenant_id = $1"]
            params: list[Any] = [tenant_id]
            if worker_id is not None:
                params.append(worker_id)
                clauses.append(f"worker_id = ${len(params)}")
            if status is not None:
                sv = status.value if isinstance(status, AssignmentStatus) else str(status)
                params.append(sv)
                clauses.append(f"status = ${len(params)}")
            where = " AND ".join(clauses)
            rows = await DatabaseConnection.fetch(
                f"SELECT * FROM workforce_assignments WHERE {where} ORDER BY assigned_at DESC",
                *params,
            )
            if not rows:
                results = [v for k, v in self._assignments.items() if k.startswith(f"{tenant_id}:")]
                if worker_id is not None:
                    results = [a for a in results if a.worker_id == worker_id]
                if status is not None:
                    sv = status.value if isinstance(status, AssignmentStatus) else str(status)
                    results = [a for a in results if a.status.value == sv]
                if results:
                    return results
                return []
            assignments = [_row_to_assignment(r) for r in rows]
            for a in assignments:
                self._assignments[self._assignment_key(tenant_id, a.id)] = a
            if worker_id is not None:
                assignments = [a for a in assignments if a.worker_id == worker_id]
            if status is not None:
                sv = status.value if isinstance(status, AssignmentStatus) else str(status)
                assignments = [a for a in assignments if a.status.value == sv]
            return assignments
        except Exception as exc:
            if "not initialized" in str(exc).lower() or "pool" in str(exc).lower():
                results = [v for k, v in self._assignments.items() if k.startswith(f"{tenant_id}:")]
                if worker_id is not None:
                    results = [a for a in results if a.worker_id == worker_id]
                if status is not None:
                    sv = status.value if isinstance(status, AssignmentStatus) else str(status)
                    results = [a for a in results if a.status.value == sv]
                return results
            self._log.warning("workforce.list_assignments.fallback", error=repr(exc))
            results = [v for k, v in self._assignments.items() if k.startswith(f"{tenant_id}:")]
            if worker_id is not None:
                results = [a for a in results if a.worker_id == worker_id]
            if status is not None:
                sv = status.value if isinstance(status, AssignmentStatus) else str(status)
                results = [a for a in results if a.status.value == sv]
            return results


__all__ = ["WorkforceRepository"]
