from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

router = APIRouter(prefix="/resilience", tags=["resilience"])

_breakers: dict[str, CircuitBreaker] = {}


def _breaker(name: str) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name=name, config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=15))
    return _breakers[name]


@router.get("/circuit/{name}")
async def get_circuit(request: Request, name: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    cb = _breaker(f"{tenant_id}:{name}")
    return {"name": name, "tenant_id": tenant_id, **cb.get_metrics()}


@router.post("/circuit/{name}/reset")
async def reset_circuit(request: Request, name: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    cb = _breaker(f"{tenant_id}:{name}")
    cb.reset()
    return {"name": name, "status": "reset", **cb.get_metrics()}


@router.get("/retry-policy")
async def retry_policy(request: Request, _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {"retry_count": 3, "backoff": "exponential", "jitter": 0.2, "retryable": ["timeout", "transient", "429", "503"], "non_retryable": ["400", "401", "403", "404", "validation"]}


@router.get("/dead-letter")
async def dead_letter_info(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # Failed executions that need diagnosis — delegates to mission/workflow failed lists
    return {"tenant_id": tenant_id, "note": "Failed executions are in /missions, /workflows, /long-missions; resilience escalates via audit chain"}
