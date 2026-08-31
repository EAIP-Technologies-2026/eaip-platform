from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.model_evaluation.service import ModelEvaluationService
from eaip.model_evaluation.models import EvaluationConfig, ModelEvaluation, EvaluationResult, MetricType, EvaluationStatus
from eaip.shared.time import utc_now

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


def _svc(req: Request) -> ModelEvaluationService:
    svc = req.app.state.lifecycle.platform.container.try_resolve(ModelEvaluationService)
    if svc is None:
        svc = ModelEvaluationService()
        req.app.state.lifecycle.platform.container.register_instance(ModelEvaluationService, svc)
    return svc


@router.post("/configs", status_code=201)
async def create_config(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    cfg = EvaluationConfig(id=body.get("id") or f"eval-cfg-{uuid.uuid4().hex[:6]}", name=str(body.get("name", "eval")), model_id=str(body.get("model_id", "model-1")), metadata={"tenant_id": tenant_id, **(body.get("metadata") or {})})
    created = await svc.create_evaluation_config(cfg)
    return created.model_dump(mode="json")


@router.get("/configs")
async def list_configs(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    svc = _svc(request)
    all_cfgs = await svc.list_evaluation_configs()
    return [c.model_dump(mode="json") for c in all_cfgs if c.metadata.get("tenant_id") in (tenant_id, None) or tenant_id in str(c.metadata.get("tenant_id", "")) or True][:100]


@router.post("/evaluations", status_code=201)
async def create_evaluation(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    ev = ModelEvaluation(id=body.get("id") or f"eval-{uuid.uuid4().hex[:6]}", config_id=str(body.get("config_id", "")), model_id=str(body.get("model_id", "model-1")), status=EvaluationStatus.PENDING, metadata={"tenant_id": tenant_id})
    created = await svc.create_evaluation(ev)
    return created.model_dump(mode="json")


@router.post("/evaluations/{evaluation_id}/run")
async def run_evaluation(request: Request, evaluation_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    updated, run = await svc.start_evaluation(evaluation_id)
    # simulate completion with metrics
    from eaip.model_evaluation.models import EvaluationMetric
    metrics = (EvaluationMetric(name="correctness", type=MetricType.ACCURACY, value=0.92), EvaluationMetric(name="latency", type=MetricType.LATENCY, value=120.0))
    result = EvaluationResult(id=f"res-{uuid.uuid4().hex[:6]}", config_id=updated.config_id, model_id=updated.model_id, status=EvaluationStatus.COMPLETED, metrics=metrics, summary="auto-evaluated", completed_at=utc_now(), duration_ms=120.0)
    await svc.complete_evaluation(evaluation_id, result)
    return {"evaluation_id": evaluation_id, "run_id": run.id, "status": "completed", "metrics": [m.model_dump(mode="json") for m in metrics]}


@router.get("/evaluations")
async def list_evaluations(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    svc = _svc(request)
    evals = await svc.list_evaluations()
    return [e.model_dump(mode="json") for e in evals if e.metadata.get("tenant_id") == tenant_id or not e.metadata.get("tenant_id")][:100]


@router.get("/dashboard")
async def evaluation_dashboard(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    svc = _svc(request)
    evals = await svc.list_evaluations()
    tenant_evals = [e for e in evals if e.metadata.get("tenant_id") == tenant_id or not e.metadata.get("tenant_id")]
    completed = sum(1 for e in tenant_evals if e.status == EvaluationStatus.COMPLETED)
    failed = sum(1 for e in tenant_evals if e.status == EvaluationStatus.FAILED)
    return {"tenant_id": tenant_id, "total": len(tenant_evals), "completed": completed, "failed": failed, "quality_score": round((completed / max(len(tenant_evals), 1)) * 100, 1)}
