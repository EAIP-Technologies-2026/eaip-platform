"""Digital Workforce 2.0 HTTP router — prefix /workforce2.

Tenant-scoped via :func:`eaip.http.dependencies.get_tenant_id`.
Backed by :class:`eaip.workforce.digital_service.DigitalWorkforceService`
with in-memory dict storage keyed ``tenant_id:employee_id``.

Endpoints:
    POST   /workforce2/employees
    GET    /workforce2/employees
    GET    /workforce2/employees/{employee_id}
    POST   /workforce2/employees/{employee_id}/performance
    POST   /workforce2/match
    GET    /workforce2/capacity
    POST   /workforce2/assignments
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.logging.context import get_logger
from eaip.workforce.digital_models import DigitalEmployee
from eaip.workforce.digital_service import DigitalWorkforceService

router = APIRouter(prefix="/workforce2", tags=["workforce2"])
log = get_logger("eaip.http.routers.digital_workforce")


def _service(request: Request) -> DigitalWorkforceService:
    svc = request.app.state.lifecycle.platform.container.try_resolve(DigitalWorkforceService)  # type: ignore[union-attr]
    if svc is not None:
        return svc  # type: ignore[no-any-return]
    # fallback: lazily create and register
    svc = DigitalWorkforceService()
    try:
        request.app.state.lifecycle.platform.container.register_instance(DigitalWorkforceService, svc)  # type: ignore[union-attr]
    except Exception:
        pass
    return svc


def _employee_to_dict(emp: DigitalEmployee) -> dict[str, Any]:
    return {
        "employee_id": emp.employee_id,
        "employeeId": emp.employee_id,
        "tenant_id": emp.tenant_id,
        "tenantId": emp.tenant_id,
        "name": emp.name,
        "role": emp.role,
        "department": emp.department,
        "responsibilities": list(emp.responsibilities),
        "capabilities": list(emp.capabilities),
        "skills": dict(emp.skills),
        "proficiency": emp.proficiency,
        "availability": emp.availability,
        "workload": emp.workload,
        "goals": list(emp.goals),
        "supervisor": emp.supervisor,
        "permissions": list(emp.permissions),
        "risk_level": emp.risk_level,
        "riskLevel": emp.risk_level,
        "performance": dict(emp.performance),
        "status": emp.status,
        "learning_history": list(emp.learning_history),
        "learningHistory": list(emp.learning_history),
        "created_at": emp.created_at.isoformat(),
        "createdAt": emp.created_at.isoformat(),
        "updated_at": emp.updated_at.isoformat(),
        "updatedAt": emp.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /employees — create
# ---------------------------------------------------------------------------


@router.post("/employees", status_code=201)
async def create_employee(
    request: Request,
    body: dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    svc = _service(request)
    employee_id = str(body.get("employee_id") or body.get("employeeId") or f"emp-{uuid.uuid4().hex[:8]}")
    # build kwargs, accepting both snake and camel keys
    kwargs: dict[str, Any] = {
        "employee_id": employee_id,
        "tenant_id": tenant_id,
        "name": str(body.get("name") or body.get("employeeName") or employee_id),
        "role": str(body.get("role", "")),
        "department": str(body.get("department", "")),
        "responsibilities": tuple(body.get("responsibilities") or body.get("responsibilitiesList") or []),
        "capabilities": tuple(body.get("capabilities") or []),
        "skills": body.get("skills") or {},
        "proficiency": float(body.get("proficiency", 0.5)),
        "availability": str(body.get("availability", "available")),
        "workload": float(body.get("workload", 0.0)),
        "goals": tuple(body.get("goals") or []),
        "supervisor": str(body.get("supervisor", "")),
        "permissions": tuple(body.get("permissions") or []),
        "risk_level": str(body.get("risk_level") or body.get("riskLevel") or "low"),
        "performance": body.get("performance") or {},
        "status": str(body.get("status", "active")),
        "learning_history": tuple(body.get("learning_history") or body.get("learningHistory") or []),
    }
    try:
        employee = DigitalEmployee.model_validate(kwargs)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        created = svc.create_employee(employee)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    log.info("digital_workforce.employee_created", employee_id=created.employee_id, tenant_id=tenant_id)
    return _employee_to_dict(created)


# ---------------------------------------------------------------------------
# GET /employees — list
# ---------------------------------------------------------------------------


@router.get("/employees")
async def list_employees(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
    availability: str | None = None,
    status: str | None = None,
    skill: str | None = None,
) -> list[dict[str, Any]]:
    svc = _service(request)
    employees = svc.list_for_tenant(tenant_id)
    if availability:
        employees = [e for e in employees if e.availability == availability]
    if status:
        employees = [e for e in employees if e.status == status]
    if skill:
        employees = [e for e in employees if skill in e.skills]
    return [_employee_to_dict(e) for e in employees]


# ---------------------------------------------------------------------------
# GET /employees/{employee_id}
# ---------------------------------------------------------------------------


@router.get("/employees/{employee_id}")
async def get_employee(
    request: Request,
    employee_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    svc = _service(request)
    emp = svc.get(employee_id, tenant_id)
    if emp is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"employee {employee_id!r} not found")
    return _employee_to_dict(emp)


# ---------------------------------------------------------------------------
# POST /employees/{employee_id}/performance — track performance
# ---------------------------------------------------------------------------


@router.post("/employees/{employee_id}/performance")
async def track_performance(
    request: Request,
    employee_id: str,
    body: dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    svc = _service(request)
    metrics = body.get("metrics") if isinstance(body.get("metrics"), dict) else body
    # remove known non-metric keys if using full body fallback
    if metrics is body:
        metrics = {k: v for k, v in body.items() if k not in {"employee_id", "tenant_id"}}
    if not metrics:
        raise HTTPException(status_code=400, detail="metrics required")
    updated = svc.track_performance(employee_id, tenant_id, metrics)
    if updated is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"employee {employee_id!r} not found")
    log.info("digital_workforce.performance_tracked", employee_id=employee_id, tenant_id=tenant_id)
    return _employee_to_dict(updated)


# ---------------------------------------------------------------------------
# POST /match — skill matching
# ---------------------------------------------------------------------------


@router.post("/match")
async def match_skill(
    request: Request,
    body: dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    svc = _service(request)
    raw = body.get("task_requirements") or body.get("taskRequirements") or body.get("requirements") or body.get("skills") or {}
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="task_requirements must be a dict[str, float]")
    try:
        requirements: dict[str, float] = {str(k): float(v) for k, v in raw.items()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not requirements:
        raise HTTPException(status_code=400, detail="task_requirements must not be empty")
    matches = svc.match_skill(tenant_id, requirements)
    return [{"employee_id": emp_id, "employeeId": emp_id, "score": score} for emp_id, score in matches]


# ---------------------------------------------------------------------------
# GET /capacity
# ---------------------------------------------------------------------------


@router.get("/capacity")
async def get_capacity(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    svc = _service(request)
    return svc.get_capacity(tenant_id)


# ---------------------------------------------------------------------------
# POST /assignments — plan workload-aware assignments
# ---------------------------------------------------------------------------


@router.post("/assignments")
async def plan_assignments(
    request: Request,
    body: dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    svc = _service(request)
    tasks = body.get("tasks")
    if tasks is None:
        # allow single task body
        if "task_requirements" in body or "taskRequirements" in body or "task_description" in body:
            tasks = [body]
        else:
            raise HTTPException(status_code=400, detail="tasks list required")
    if not isinstance(tasks, list):
        raise HTTPException(status_code=400, detail="tasks must be a list")
    if not tasks:
        return []
    for t in tasks:
        if not isinstance(t, dict):
            raise HTTPException(status_code=400, detail="each task must be an object")
    created = svc.plan_assignments(tenant_id, tasks)
    return [
        {
            "assignment_id": a.assignment_id,
            "assignmentId": a.assignment_id,
            "tenant_id": a.tenant_id,
            "employee_id": a.employee_id,
            "employeeId": a.employee_id,
            "task_id": a.task_id,
            "taskId": a.task_id,
            "task_description": a.task_description,
            "taskDescription": a.task_description,
            "task_requirements": a.task_requirements,
            "taskRequirements": a.task_requirements,
            "status": a.status,
            "priority": a.priority,
            "workload_cost": a.workload_cost,
            "workloadCost": a.workload_cost,
            "assigned_at": a.assigned_at.isoformat(),
            "assignedAt": a.assigned_at.isoformat(),
        }
        for a in created
    ]


__all__ = ["router"]
