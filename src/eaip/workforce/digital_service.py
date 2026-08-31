"""DigitalWorkforceService — tenant-isolated digital employee management.

Storage is an in-memory dict keyed ``tenant_id:employee_id``. All models are
frozen Pydantic; updates use ``model_copy``. Events are published via an
injected EventBus when available, mirroring :mod:`eaip.workforce.worker`.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from eaip.events.event import DomainEvent
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now
from eaip.workforce.digital_models import DigitalEmployee, WorkforceAssignment2, WorkforceCapacity2

log = get_logger("eaip.workforce.digital_service")


# ---------------------------------------------------------------------------
# Domain events for Digital Workforce 2.0
# ---------------------------------------------------------------------------


class DigitalEmployeeCreated(DomainEvent):
    event_type: str = "workforce.employee.created"  # type: ignore[assignment]
    employee_id: str = ""
    tenant_id: str = ""
    name: str = ""
    role: str = ""


class DigitalEmployeeUpdated(DomainEvent):
    event_type: str = "workforce.employee.updated"  # type: ignore[assignment]
    employee_id: str = ""
    tenant_id: str = ""
    updated_fields: tuple[str, ...] = ()


class DigitalEmployeePerformanceTracked(DomainEvent):
    event_type: str = "workforce.employee.performance.tracked"  # type: ignore[assignment]
    employee_id: str = ""
    tenant_id: str = ""
    metrics: dict[str, Any] = {}


class WorkforceAssignmentsPlanned(DomainEvent):
    event_type: str = "workforce.assignments.planned"  # type: ignore[assignment]
    tenant_id: str = ""
    count: int = 0


class WorkforceCapacityQueried(DomainEvent):
    event_type: str = "workforce.capacity.queried"  # type: ignore[assignment]
    tenant_id: str = ""
    total: int = 0
    available: int = 0


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class DigitalWorkforceService:
    """Tenant-isolated service for digital employees."""

    def __init__(self, event_bus: Any | None = None) -> None:
        self._store: dict[str, DigitalEmployee] = {}
        self._assignments: dict[str, WorkforceAssignment2] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.workforce.digital_service")

    # -- keying --

    @staticmethod
    def _key(tenant_id: str, employee_id: str) -> str:
        return f"{tenant_id}:{employee_id}"

    @staticmethod
    def _assignment_key(tenant_id: str, assignment_id: str) -> str:
        return f"{tenant_id}:{assignment_id}"

    # -- CRUD --

    def create_employee(self, employee: DigitalEmployee) -> DigitalEmployee:
        """Create a new digital employee.

        Args:
            employee: Fully-populated :class:`DigitalEmployee` (must include
                tenant_id and employee_id).

        Returns:
            The stored employee.

        Raises:
            ValueError: If employee_id already exists for the tenant.
        """
        key = self._key(employee.tenant_id, employee.employee_id)
        if key in self._store:
            raise ValueError(f"employee {employee.employee_id!r} already exists for tenant {employee.tenant_id!r}")
        # stamp timestamps
        now = utc_now()
        stored = employee.model_copy(update={"created_at": now, "updated_at": now})
        self._store[key] = stored
        self._log.info("digital_employee.created", employee_id=stored.employee_id, tenant_id=stored.tenant_id)
        self._publish(
            DigitalEmployeeCreated(
                employee_id=stored.employee_id,
                tenant_id=stored.tenant_id,
                name=stored.name,
                role=stored.role,
            )
        )
        return stored

    def get(self, employee_id: str, tenant_id: str) -> DigitalEmployee | None:
        """Retrieve an employee by id within a tenant."""
        return self._store.get(self._key(tenant_id, employee_id))

    def list_for_tenant(self, tenant_id: str) -> list[DigitalEmployee]:
        """List all employees for a tenant."""
        prefix = f"{tenant_id}:"
        return [v for k, v in self._store.items() if k.startswith(prefix)]

    def update(self, employee_id: str, tenant_id: str, updates: dict[str, Any]) -> DigitalEmployee | None:
        """Update an employee with a partial dict; returns new frozen copy.

        Returns ``None`` if not found.
        """
        key = self._key(tenant_id, employee_id)
        existing = self._store.get(key)
        if existing is None:
            return None
        # prevent tenant/employee_id mutation via updates
        updates = {k: v for k, v in updates.items() if k not in {"tenant_id", "employee_id", "created_at"}}
        # coerce tuple fields if list provided
        for tf in ("responsibilities", "capabilities", "goals", "permissions"):
            if tf in updates and isinstance(updates[tf], list):
                updates[tf] = tuple(updates[tf])
        if "learning_history" in updates and isinstance(updates["learning_history"], list):
            updates["learning_history"] = tuple(updates["learning_history"])
        updates["updated_at"] = utc_now()
        try:
            new = existing.model_copy(update=updates)
        except Exception as exc:
            raise ValueError(str(exc)) from exc
        self._store[key] = new
        self._log.info("digital_employee.updated", employee_id=employee_id, tenant_id=tenant_id, fields=list(updates.keys()))
        self._publish(
            DigitalEmployeeUpdated(
                employee_id=employee_id,
                tenant_id=tenant_id,
                updated_fields=tuple(k for k in updates.keys() if k != "updated_at"),
            )
        )
        return new

    def delete(self, employee_id: str, tenant_id: str) -> bool:
        """Delete an employee; returns True if removed."""
        key = self._key(tenant_id, employee_id)
        return self._store.pop(key, None) is not None

    # -- matching --

    def match_skill(
        self,
        tenant_id: str,
        task_requirements: dict[str, float],
    ) -> list[tuple[str, float]]:
        """Match employees against skill requirements.

        Scoring: ``sum(employee.skills[skill] * weight for skill, weight in requirements)``.
        Employees without matching skills score 0. Results sorted descending by score.
        Only employees with ``status == active`` are considered.

        Args:
            tenant_id: Tenant scope.
            task_requirements: Mapping skill -> weight/importance.

        Returns:
            List of ``(employee_id, score)`` sorted descending.
        """
        employees = self.list_for_tenant(tenant_id)
        if not task_requirements:
            return []
        # normalise weights to floats
        req = {k: float(v) for k, v in task_requirements.items()}
        scored: list[tuple[str, float]] = []
        for emp in employees:
            if emp.status != "active":
                continue
            score = 0.0
            for skill, weight in req.items():
                prof = emp.skills.get(skill)
                if prof is not None:
                    # proficiency * weight as per spec
                    score += float(prof) * float(weight)
            # optionally factor aggregate proficiency when no direct skill match but employee has capabilities?
            scored.append((emp.employee_id, round(score, 6)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def plan_assignments(
        self,
        tenant_id: str,
        tasks: list[dict[str, Any]],
    ) -> list[WorkforceAssignment2]:
        """Plan workload-aware assignments for a batch of tasks.

        Each task dict may contain ``task_id``, ``task_description``,
        ``task_requirements`` (skill->weight), ``priority`` and
        ``workload_cost``. Employees are selected for lowest workload first
        among those with highest skill match. Assignments increment employee
        workload (capped at 1.0) to model capacity.

        Args:
            tenant_id: Tenant scope.
            tasks: List of task dicts.

        Returns:
            List of created :class:`WorkforceAssignment2`.
        """
        # sort tasks by priority descending
        ordered = sorted(tasks, key=lambda t: int(t.get("priority", 0)), reverse=True)
        created: list[WorkforceAssignment2] = []
        for task in ordered:
            req: dict[str, float] = {}
            raw_req = task.get("task_requirements") or task.get("requirements") or {}
            if isinstance(raw_req, dict):
                req = {str(k): float(v) for k, v in raw_req.items()}
            workload_cost = float(task.get("workload_cost", task.get("workloadCost", 0.1)))
            workload_cost = max(0.0, min(1.0, workload_cost))
            task_id = str(task.get("task_id") or task.get("taskId") or task.get("id") or f"task-{uuid.uuid4().hex[:8]}")
            task_description = str(task.get("task_description") or task.get("taskDescription") or task.get("description") or "")

            # find candidates: available employees not overloaded
            candidates = [e for e in self.list_for_tenant(tenant_id) if e.status == "active" and e.availability == "available"]
            # if no available, fall back to busy but not offline
            if not candidates:
                candidates = [e for e in self.list_for_tenant(tenant_id) if e.status == "active" and e.availability != "offline"]

            # score each candidate
            scored: list[tuple[DigitalEmployee, float]] = []
            for emp in candidates:
                # capacity check: workload + cost must not exceed 1.0
                if emp.workload + workload_cost > 1.0 + 1e-9:
                    continue
                skill_score = 0.0
                for skill, w in req.items():
                    prof = emp.skills.get(skill)
                    if prof is not None:
                        skill_score += float(prof) * float(w)
                # tie-breaker: lower workload is better -> use negative workload
                # composite: skill_score primary, workload secondary
                scored.append((emp, skill_score))

            if not scored:
                # no eligible employee; skip task (could also create unassigned)
                continue

            # sort: highest skill_score first, then lowest workload
            scored.sort(key=lambda x: (x[1], -x[0].workload), reverse=True)
            # pick best that is not overloaded; already filtered
            chosen = scored[0][0]
            # create assignment
            assignment = WorkforceAssignment2(
                assignment_id=f"asgn-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                employee_id=chosen.employee_id,
                task_id=task_id,
                task_description=task_description,
                task_requirements=req,
                status="assigned",
                priority=int(task.get("priority", 0)),
                workload_cost=workload_cost,
            )
            self._assignments[self._assignment_key(tenant_id, assignment.assignment_id)] = assignment
            created.append(assignment)
            # increment chosen workload
            new_workload = min(1.0, chosen.workload + workload_cost)
            new_availability = chosen.availability
            if new_workload >= 0.95:
                new_availability = "busy"
            updated = chosen.model_copy(update={"workload": round(new_workload, 4), "availability": new_availability, "updated_at": utc_now()})
            self._store[self._key(tenant_id, chosen.employee_id)] = updated

        if created:
            self._publish(WorkforceAssignmentsPlanned(tenant_id=tenant_id, count=len(created)))
        return created

    # -- capacity --

    def get_capacity(self, tenant_id: str) -> dict[str, Any]:
        """Return capacity dict for a tenant.

        Returns:
            Dict with total/available/busy/offline/utilization plus workload
            aggregates, suitable for JSON response.
        """
        employees = self.list_for_tenant(tenant_id)
        total = len(employees)
        available = sum(1 for e in employees if e.availability == "available" and e.status == "active")
        busy = sum(1 for e in employees if e.availability == "busy" and e.status == "active")
        offline = sum(1 for e in employees if e.availability == "offline" or e.status != "active")
        total_workload = round(sum(float(e.workload) for e in employees), 4)
        available_capacity = round(sum(max(0.0, 1.0 - float(e.workload)) for e in employees if e.status == "active"), 4)
        utilization = round(total_workload / total, 4) if total else 0.0
        result = {
            "tenant_id": tenant_id,
            "total": total,
            "available": available,
            "busy": busy,
            "offline": offline,
            "utilization": utilization,
            "total_workload": total_workload,
            "available_capacity": available_capacity,
            "timestamp": utc_now().isoformat(),
        }
        self._publish(WorkforceCapacityQueried(tenant_id=tenant_id, total=total, available=available))
        return result

    def get_capacity_model(self, tenant_id: str) -> WorkforceCapacity2:
        """Return a typed :class:`WorkforceCapacity2` snapshot."""
        d = self.get_capacity(tenant_id)
        return WorkforceCapacity2(
            tenant_id=tenant_id,
            total=d["total"],
            available=d["available"],
            busy=d["busy"],
            offline=d["offline"],
            utilization=d["utilization"],
            total_workload=d["total_workload"],
            available_capacity=d["available_capacity"],
        )

    # -- performance --

    def track_performance(
        self,
        employee_id: str,
        tenant_id: str,
        metrics: dict[str, Any],
    ) -> DigitalEmployee | None:
        """Track performance metrics for an employee.

        Merges metrics into ``performance`` dict and appends a learning_history
        entry.

        Args:
            employee_id: Employee identifier.
            tenant_id: Tenant scope.
            metrics: Performance metrics to merge.

        Returns:
            Updated employee or None if not found.
        """
        key = self._key(tenant_id, employee_id)
        existing = self._store.get(key)
        if existing is None:
            return None
        merged_performance = {**existing.performance, **metrics}
        history_entry: dict[str, Any] = {"timestamp": utc_now().isoformat(), "metrics": metrics}
        new_history = tuple([*existing.learning_history, history_entry])
        updated = existing.model_copy(
            update={
                "performance": merged_performance,
                "learning_history": new_history,
                "updated_at": utc_now(),
            }
        )
        self._store[key] = updated
        self._log.info("digital_employee.performance", employee_id=employee_id, tenant_id=tenant_id)
        self._publish(
            DigitalEmployeePerformanceTracked(
                employee_id=employee_id,
                tenant_id=tenant_id,
                metrics=metrics,
            )
        )
        return updated

    # -- assignments listing --

    def list_assignments(self, tenant_id: str) -> list[WorkforceAssignment2]:
        prefix = f"{tenant_id}:"
        return [v for k, v in self._assignments.items() if k.startswith(prefix)]

    # -- internal publish --

    def _publish(self, event: DomainEvent) -> None:
        if self._event_bus is None:
            return
        try:
            # mirror workforce/worker.py pattern: create_task without awaiting
            asyncio.create_task(self._event_bus.publish(event))  # type: ignore[attr-defined]
        except RuntimeError:
            # no running loop (e.g. tests / sync context) — try sync publish or ignore
            try:
                maybe = self._event_bus.publish(event)
                if asyncio.iscoroutine(maybe):
                    # schedule when loop available
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(maybe)  # type: ignore[arg-type]
                    except Exception:
                        pass
            except Exception:
                self._log.warning("event.publish.failed", event_type=type(event).__name__)
        except Exception:
            self._log.warning("event.publish.failed", event_type=type(event).__name__)


__all__ = [
    "DigitalEmployeeCreated",
    "DigitalEmployeePerformanceTracked",
    "DigitalEmployeeUpdated",
    "DigitalWorkforceService",
    "WorkforceAssignmentsPlanned",
    "WorkforceCapacityQueried",
]
