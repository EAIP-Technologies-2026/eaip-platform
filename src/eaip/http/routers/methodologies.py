"""Methodologies router — prefix /methodologies.

Tenant-scoped via :func:`eaip.http.dependencies.get_tenant_id`.
Backed by :class:`eaip.methodology.registry.MethodologyRegistry`.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.logging.context import get_logger
from eaip.methodology.models import MethodologyCategory, MethodologyRecord
from eaip.methodology.registry import MethodologyRegistry

router = APIRouter(prefix="/methodologies", tags=["methodologies"])
log = get_logger("eaip.http.routers.methodologies")


def _registry(request: Request) -> MethodologyRegistry:
    reg = request.app.state.lifecycle.platform.container.try_resolve(MethodologyRegistry)  # type: ignore[union-attr]
    if reg is not None:
        return reg  # type: ignore[no-any-return]
    reg = MethodologyRegistry()
    try:
        request.app.state.lifecycle.platform.container.register_instance(MethodologyRegistry, reg)  # type: ignore[union-attr]
    except Exception:
        pass
    return reg


def _record_to_dict(r: MethodologyRecord) -> dict[str, Any]:
    return {
        "methodology_id": r.methodology_id,
        "methodologyId": r.methodology_id,
        "tenant_id": r.tenant_id,
        "tenantId": r.tenant_id,
        "name": r.name,
        "version": r.version,
        "category": r.category.value if hasattr(r.category, "value") else str(r.category),
        "provider": r.provider,
        "capabilities": list(r.capabilities),
        "input_requirements": r.input_requirements,
        "inputRequirements": r.input_requirements,
        "output_contract": r.output_contract,
        "outputContract": r.output_contract,
        "cost": r.cost,
        "latency": r.latency,
        "reliability": r.reliability,
        "benchmark_score": r.benchmark_score,
        "benchmarkScore": r.benchmark_score,
        "supported_domains": list(r.supported_domains),
        "supportedDomains": list(r.supported_domains),
        "lifecycle_status": r.lifecycle_status,
        "lifecycleStatus": r.lifecycle_status,
        "created_at": r.created_at.isoformat(),
        "createdAt": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
        "updatedAt": r.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /methodologies — create / register (with versioning)
# ---------------------------------------------------------------------------


@router.post("", status_code=201)
@router.post("/", status_code=201, include_in_schema=False)
async def create_methodology(
    request: Request,
    body: dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    reg = _registry(request)
    methodology_id = str(body.get("methodology_id") or body.get("methodologyId") or f"mth-{uuid.uuid4().hex[:8]}")
    raw_category = str(body.get("category", "reasoning"))
    try:
        category = MethodologyCategory(raw_category.lower())
    except ValueError:
        # allow unknown but map to reasoning as fallback? Better to 400.
        raise HTTPException(status_code=400, detail=f"invalid category {raw_category!r}. Must be one of {[c.value for c in MethodologyCategory]}") from None

    kwargs: dict[str, Any] = {
        "methodology_id": methodology_id,
        "tenant_id": tenant_id,
        "name": str(body.get("name") or methodology_id),
        "version": str(body.get("version", "1.0.0")),
        "category": category,
        "provider": str(body.get("provider", "eaip")),
        "capabilities": tuple(body.get("capabilities") or []),
        "input_requirements": body.get("input_requirements") or body.get("inputRequirements") or {},
        "output_contract": body.get("output_contract") or body.get("outputContract") or {},
        "cost": float(body.get("cost", 0.0)),
        "latency": float(body.get("latency", 0.0)),
        "reliability": float(body.get("reliability", 0.95)),
        "benchmark_score": float(body.get("benchmark_score") if "benchmark_score" in body else body.get("benchmarkScore", 0.0)),
        "supported_domains": tuple(body.get("supported_domains") or body.get("supportedDomains") or []),
        "lifecycle_status": str(body.get("lifecycle_status") or body.get("lifecycleStatus") or "active"),
    }
    try:
        record = MethodologyRecord.model_validate(kwargs)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    stored = reg.register(record)
    log.info("methodology.created", methodology_id=stored.methodology_id, version=stored.version, tenant_id=tenant_id)
    return _record_to_dict(stored)


# ---------------------------------------------------------------------------
# GET /methodologies — list
# ---------------------------------------------------------------------------


@router.get("")
@router.get("/", include_in_schema=False)
async def list_methodologies(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
    category: str | None = None,
    domain: str | None = None,
    q: str | None = None,
    query: str | None = None,
    include_deprecated: bool = False,
) -> list[dict[str, Any]]:
    reg = _registry(request)
    # allow either q or query
    search_q = (q or query or "").strip()
    if category or domain or search_q:
        results = reg.search(tenant_id, query=search_q, category=category or "", domain=domain or "", include_deprecated=include_deprecated)
    else:
        results = reg.list_for_tenant(tenant_id, include_deprecated=include_deprecated)
    return [_record_to_dict(r) for r in results]


# ---------------------------------------------------------------------------
# GET /methodologies/search — explicit search endpoint (must be before /{id})
# ---------------------------------------------------------------------------


@router.get("/search")
async def search_methodologies(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
    q: str = "",
    query: str = "",
    category: str = "",
    domain: str = "",
    include_deprecated: bool = False,
) -> list[dict[str, Any]]:
    reg = _registry(request)
    search_q = (q or query or "").strip()
    results = reg.search(tenant_id, query=search_q, category=category, domain=domain, include_deprecated=include_deprecated)
    return [_record_to_dict(r) for r in results]


# ---------------------------------------------------------------------------
# POST /methodologies/recommend — recommend sorted by benchmark
# ---------------------------------------------------------------------------


@router.post("/recommend")
async def recommend_methodologies(
    request: Request,
    body: dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    reg = _registry(request)
    task = str(body.get("task", ""))
    domain = str(body.get("domain", body.get("supportedDomain", "")))
    category = str(body.get("category", ""))
    latency_budget = body.get("latency_budget") if "latency_budget" in body else body.get("latencyBudget")
    cost_budget = body.get("cost_budget") if "cost_budget" in body else body.get("costBudget")
    limit = int(body.get("limit", 10))
    results = reg.recommend(
        tenant_id,
        task=task,
        domain=domain,
        latency_budget=float(latency_budget) if latency_budget is not None else None,
        cost_budget=float(cost_budget) if cost_budget is not None else None,
        category=category,
        limit=limit,
    )
    return [_record_to_dict(r) for r in results]


# ---------------------------------------------------------------------------
# GET /methodologies/{methodology_id}
# (also supports ?version= and ?include_deprecated)
# ---------------------------------------------------------------------------


@router.get("/{methodology_id}")
async def get_methodology(
    request: Request,
    methodology_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
    version: str | None = None,
    include_versions: bool = False,
) -> dict[str, Any]:
    reg = _registry(request)
    if include_versions:
        versions = reg.list_versions(methodology_id, tenant_id)
        if not versions:
            raise HTTPException(status_code=404, detail=f"methodology {methodology_id!r} not found")
        return {"methodology_id": methodology_id, "versions": [_record_to_dict(v) for v in versions]}
    rec = reg.get(methodology_id, tenant_id, version=version)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"methodology {methodology_id!r} not found")
    return _record_to_dict(rec)


# ---------------------------------------------------------------------------
# GET /methodologies/{methodology_id}/versions — version history
# ---------------------------------------------------------------------------


@router.get("/{methodology_id}/versions")
async def list_methodology_versions(
    request: Request,
    methodology_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    reg = _registry(request)
    versions = reg.list_versions(methodology_id, tenant_id)
    if not versions:
        raise HTTPException(status_code=404, detail=f"methodology {methodology_id!r} not found")
    return [_record_to_dict(v) for v in versions]


# ---------------------------------------------------------------------------
# POST /methodologies/{methodology_id}/evaluate — update reliability/latency
# ---------------------------------------------------------------------------


@router.post("/{methodology_id}/evaluate")
async def evaluate_methodology(
    request: Request,
    methodology_id: str,
    body: dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    reg = _registry(request)
    version = body.get("version")
    metrics = body.get("metrics") if isinstance(body.get("metrics"), dict) else {k: v for k, v in body.items() if k not in {"version", "methodology_id"}}
    if not metrics:
        raise HTTPException(status_code=400, detail="metrics required (reliability/latency/benchmark_score/cost)")
    updated = reg.evaluate(methodology_id, tenant_id, metrics, version=str(version) if version else None)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"methodology {methodology_id!r} not found")
    log.info("methodology.evaluated", methodology_id=methodology_id, tenant_id=tenant_id)
    return _record_to_dict(updated)


__all__ = ["router"]
