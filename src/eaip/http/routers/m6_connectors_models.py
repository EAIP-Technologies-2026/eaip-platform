from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/m6", tags=["m6"])

_connectors: dict[str, dict[str, Any]] = {}
_capabilities: dict[str, dict[str, Any]] = {}
_health: dict[str, dict[str, Any]] = {}
_models: dict[str, dict[str, Any]] = {}
_routing_decisions: dict[str, list[dict[str, Any]]] = {}
_experiments: dict[str, dict[str, Any]] = {}
_experiment_results: dict[str, list[dict[str, Any]]] = {}
_evaluations: dict[str, list[dict[str, Any]]] = {}


def _k(tenant_id: str, entity_id: str) -> str:
    return f"{tenant_id}:{entity_id}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _list_for_tenant(store: dict[str, Any], tenant_id: str) -> list[dict[str, Any]]:
    prefix = f"{tenant_id}:"
    return [v for k, v in store.items() if k.startswith(prefix)]


# ── Connectors ────────────────────────────────────────────────────────
@router.post("/connectors/register", status_code=201)
async def register_connector(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    connector_type = str(body.get("connector_type", "")).strip()
    name = str(body.get("name", "")).strip()
    if not connector_type or not name:
        raise HTTPException(status_code=400, detail="connector_type and name required")
    credential_ref = str(body.get("credential_ref", ""))
    # secret safety: reject raw credentials
    if any(k in credential_ref.lower() for k in ["sk-", "bearer ", "password"]):
        raise HTTPException(status_code=400, detail="Use vault:// credential reference, not raw secrets")
    conn_id = f"conn-{uuid.uuid4().hex[:8]}"
    rec: dict[str, Any] = {
        "id": conn_id, "tenant_id": tenant_id, "connector_type": connector_type,
        "name": name, "description": str(body.get("description", "")),
        "credential_ref": credential_ref, "config": body.get("config", {}),
        "status": "registered", "health_status": "unknown", "created_at": _now(),
        "capabilities": [], "mode": "synthetic" if not credential_ref or credential_ref.startswith("vault://synthetic") else "configured",
    }
    _connectors[_k(tenant_id, conn_id)] = rec
    return rec


@router.get("/connectors")
async def list_connectors(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_connectors, tenant_id)


@router.get("/connectors/{connector_id}")
async def get_connector(connector_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _connectors.get(_k(tenant_id, connector_id))
    if rec is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    return rec


@router.post("/connectors/{connector_id}/connect")
async def connect_connector(connector_id: str, body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _connectors.get(_k(tenant_id, connector_id))
    if rec is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    cred = str(body.get("credential_ref", rec.get("credential_ref", "")))
    if cred and not cred.startswith("vault://"):
        raise HTTPException(status_code=400, detail="Credential must be vault:// reference")
    rec = {**rec, "status": "connected", "health_status": "healthy", "connected_at": _now()}
    _connectors[_k(tenant_id, connector_id)] = rec
    return rec


@router.post("/connectors/{connector_id}/disconnect")
async def disconnect_connector(connector_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _connectors.get(_k(tenant_id, connector_id))
    if rec is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    rec = {**rec, "status": "disconnected", "disconnected_at": _now()}
    _connectors[_k(tenant_id, connector_id)] = rec
    return rec


@router.get("/connectors/{connector_id}/health")
async def get_connector_health(connector_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _health.get(_k(tenant_id, connector_id))
    if rec is None:
        return {"connector_id": connector_id, "tenant_id": tenant_id, "availability": 0.0, "error_rate": 0.0, "auth_status": "not_checked", "circuit_state": "closed", "degradation_level": "none"}
    return rec


@router.post("/connectors/{connector_id}/invoke")
async def invoke_connector(connector_id: str, body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _connectors.get(_k(tenant_id, connector_id))
    if rec is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    if rec.get("status") != "connected":
        raise HTTPException(status_code=409, detail="Connector not connected")
    operation = str(body.get("operation", "")).strip()
    if not operation:
        raise HTTPException(status_code=400, detail="operation required")
    # policy check would go here
    return {"connector_id": connector_id, "operation": operation, "params": body.get("params", {}), "result": {"synthetic": True, "operation": operation, "message": f"Synthetic execution of {operation} on {rec['connector_type']}"}, "executed_at": _now(), "mode": "synthetic"}


@router.get("/connectors/capabilities")
async def list_all_capabilities(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_capabilities, tenant_id)


@router.get("/connectors/{connector_id}/capabilities")
async def get_connector_capabilities(connector_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    cap = _capabilities.get(_k(tenant_id, connector_id))
    if cap is None:
        return {"connector_id": connector_id, "operations": [], "permissions": [], "data_classes": []}
    return cap


@router.post("/connectors/{connector_id}/capabilities", status_code=201)
async def register_capability(connector_id: str, body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    cap: dict[str, Any] = {
        "connector_id": connector_id, "tenant_id": tenant_id,
        "operations": body.get("operations", []), "permissions": body.get("permissions", []),
        "data_classes": body.get("data_classes", []), "cost_estimate": body.get("cost_estimate", 0),
        "latency_estimate": body.get("latency_estimate", 0), "registered_at": _now(),
    }
    _capabilities[_k(tenant_id, connector_id)] = cap
    return cap


@router.get("/connectors/available")
async def list_available_connectors(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [v for v in _list_for_tenant(_connectors, tenant_id) if v.get("status") in ("connected", "registered")]


@router.post("/connectors/health/{connector_id}/update")
async def update_connector_health(connector_id: str, body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    report: dict[str, Any] = {
        "connector_id": connector_id, "tenant_id": tenant_id,
        "availability": float(body.get("availability", 1.0)),
        "error_rate": float(body.get("error_rate", 0.0)),
        "latency_ms": float(body.get("latency_ms", 0)),
        "auth_status": str(body.get("auth_status", "valid")),
        "circuit_state": str(body.get("circuit_state", "closed")),
        "degradation_level": str(body.get("degradation_level", "none")),
        "checked_at": _now(), "success": bool(body.get("success", True)),
    }
    _health[_k(tenant_id, connector_id)] = report
    return report


@router.get("/connectors/unhealthy")
async def list_unhealthy_connectors(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [v for v in _list_for_tenant(_health, tenant_id) if v.get("degradation_level", "none") != "none"]


@router.post("/connectors/policy/check")
async def check_connector_policy(body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    connector_id = str(body.get("connector_id", ""))
    operation = str(body.get("operation", ""))
    data_class = str(body.get("data_classification", "internal"))
    if data_class == "restricted" and operation in ("delete", "export_all"):
        return {"decision": "DENY", "reason": f"Operation {operation} denied for {data_class} data", "requires_approval": False}
    if data_class == "confidential":
        return {"decision": "APPROVAL", "reason": "Confidential data requires approval", "requires_approval": True}
    return {"decision": "ALLOW", "reason": "Policy check passed", "requires_approval": False}


# ── Models ────────────────────────────────────────────────────────────
@router.post("/models/register", status_code=201)
async def register_model(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    provider = str(body.get("provider", "")).strip()
    model_name = str(body.get("model_name", "")).strip()
    if not provider or not model_name:
        raise HTTPException(status_code=400, detail="provider and model_name required")
    model_id = str(body.get("id", f"model-{uuid.uuid4().hex[:8]}"))
    rec: dict[str, Any] = {
        "id": model_id, "tenant_id": tenant_id, "provider": provider, "model_name": model_name,
        "version": str(body.get("version", "1.0.0")),
        "capabilities": body.get("capabilities", ["chat"]),
        "context_limit": int(body.get("context_limit", 4096)),
        "cost_per_1k_tokens": float(body.get("cost_per_1k_tokens", 0.01)),
        "quality_score": float(body.get("quality_score", 0.8)),
        "availability": float(body.get("availability", 1.0)),
        "privacy_level": str(body.get("privacy_level", "private")),
        "locality": str(body.get("locality", "cloud")),
        "supported_tools": body.get("supported_tools", []),
        "supported_modalities": body.get("supported_modalities", ["text"]),
        "status": "active", "created_at": _now(),
    }
    _models[_k(tenant_id, model_id)] = rec
    return rec


@router.get("/models")
async def list_models(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_models, tenant_id)


@router.get("/models/{model_id}")
async def get_model(model_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _models.get(_k(tenant_id, model_id))
    if rec is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return rec


@router.delete("/models/{model_id}")
async def delete_model(model_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, model_id)
    if key not in _models:
        raise HTTPException(status_code=404, detail="Model not found")
    del _models[key]
    return {"deleted": model_id}


@router.post("/models/route")
async def route_model(body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    task_type = str(body.get("task_type", "chat"))
    data_class = str(body.get("data_classification", "internal"))
    cost_limit = body.get("cost_limit")
    models = _list_for_tenant(_models, tenant_id)
    if not models:
        raise HTTPException(status_code=404, detail="No models registered for tenant")
    # Privacy-aware routing
    if data_class in ("restricted", "confidential"):
        private = [m for m in models if m.get("privacy_level") == "private"]
        if private:
            models = private
    # Cost-aware routing
    if cost_limit is not None:
        models = [m for m in models if m.get("cost_per_1k_tokens", 0) <= float(cost_limit)]
        if not models:
            models = _list_for_tenant(_models, tenant_id)
    # Select best quality among filtered
    selected = max(models, key=lambda m: m.get("quality_score", 0))
    decision: dict[str, Any] = {
        "task_type": task_type, "selected_model_id": selected["id"],
        "reason": f"Selected {selected['provider']}/{selected['model_name']} for {task_type} (data_class={data_class})",
        "alternatives": [m["id"] for m in models if m["id"] != selected["id"]],
        "created_at": _now(),
    }
    _routing_decisions.setdefault(tenant_id, []).append(decision)
    return decision


@router.post("/models/failover")
async def failover_model(body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    model_id = str(body.get("model_id", ""))
    error = str(body.get("error", ""))
    models = _list_for_tenant(_models, tenant_id)
    current = next((m for m in models if m["id"] == model_id), None)
    if current is None:
        raise HTTPException(status_code=404, detail="Model not found")
    # Find fallback: next best model that is not the failed one
    candidates = [m for m in models if m["id"] != model_id and m.get("status") == "active"]
    if not candidates:
        raise HTTPException(status_code=409, detail="No fallback model available")
    # Policy check: never fallback to forbidden model (restricted privacy mismatch)
    fallback = max(candidates, key=lambda m: m.get("quality_score", 0))
    return {"from_model": model_id, "to_model": fallback["id"], "reason": f"Failover from {model_id}: {error}", "policy_checked": True}


@router.get("/models/{model_id}/health")
async def get_model_health(model_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    evals = _evaluations.get(_k(tenant_id, model_id), [])
    if not evals:
        return {"model_id": model_id, "availability": 1.0, "checked": False}
    avg_quality = sum(e.get("quality_score", 0) for e in evals) / len(evals)
    return {"model_id": model_id, "evaluations": len(evals), "avg_quality": avg_quality, "availability": 1.0}


@router.post("/models/{model_id}/health")
async def update_model_health(model_id: str, body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    _evaluations.setdefault(_k(tenant_id, model_id), []).append({"type": "health", **body, "recorded_at": _now()})
    return {"model_id": model_id, "updated": True}


@router.post("/models/evaluate")
async def evaluate_model(body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    model_id = str(body.get("model_id", ""))
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id required")
    rec: dict[str, Any] = {
        "id": f"eval-{uuid.uuid4().hex[:8]}", "model_id": model_id, "tenant_id": tenant_id,
        "task_type": str(body.get("task_type", "general")),
        "quality_score": float(body.get("quality_score", 0.8)),
        "latency_ms": float(body.get("latency_ms", 0)),
        "cost": float(body.get("cost", 0)),
        "success": bool(body.get("success", True)),
        "evaluated_at": _now(),
    }
    _evaluations.setdefault(_k(tenant_id, model_id), []).append(rec)
    return rec


@router.get("/models/{model_id}/evaluation")
async def get_model_evaluation(model_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    evals = _evaluations.get(_k(tenant_id, model_id), [])
    if not evals:
        return {"model_id": model_id, "evaluations": [], "avg_quality": 0}
    avg_q = sum(e.get("quality_score", 0) for e in evals) / len(evals)
    return {"model_id": model_id, "evaluations": evals, "count": len(evals), "avg_quality": avg_q}


@router.post("/models/compare")
async def compare_models(body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    model_ids: list[str] = body.get("model_ids", [])
    task_type = str(body.get("task_type", "general"))
    results = []
    for mid in model_ids:
        rec = _models.get(_k(tenant_id, mid))
        evals = _evaluations.get(_k(tenant_id, mid), [])
        avg_q = sum(e.get("quality_score", 0) for e in evals) / len(evals) if evals else (rec.get("quality_score", 0) if rec else 0)
        results.append({"model_id": mid, "avg_quality": avg_q, "evaluations": len(evals), "provider": rec.get("provider", "") if rec else ""})
    results.sort(key=lambda r: r["avg_quality"], reverse=True)
    return {"task_type": task_type, "comparison": results, "winner": results[0]["model_id"] if results else None}


@router.post("/models/experiments", status_code=201)
async def create_experiment(body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    exp_id = f"exp-{uuid.uuid4().hex[:8]}"
    rec: dict[str, Any] = {
        "id": exp_id, "tenant_id": tenant_id, "name": name,
        "models": body.get("models", []), "task_type": str(body.get("task_type", "general")),
        "traffic_split": body.get("traffic_split", {}), "status": "running", "winner": None, "created_at": _now(),
    }
    _experiments[_k(tenant_id, exp_id)] = rec
    return rec


@router.get("/models/experiments")
async def list_experiments(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_experiments, tenant_id)


@router.get("/models/experiments/{experiment_id}")
async def get_experiment(experiment_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _experiments.get(_k(tenant_id, experiment_id))
    if rec is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return rec


@router.post("/models/experiments/{experiment_id}/results")
async def record_experiment_result(experiment_id: str, body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    exp = _experiments.get(_k(tenant_id, experiment_id))
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    result: dict[str, Any] = {
        "id": f"res-{uuid.uuid4().hex[:8]}", "experiment_id": experiment_id, "tenant_id": tenant_id,
        "model_id": str(body.get("model_id", "")), "quality": float(body.get("quality", 0)),
        "latency": float(body.get("latency", 0)), "cost": float(body.get("cost", 0)),
        "success": bool(body.get("success", True)), "recorded_at": _now(),
    }
    _experiment_results.setdefault(_k(tenant_id, experiment_id), []).append(result)
    return result


@router.post("/models/experiments/{experiment_id}/promote")
async def promote_experiment_winner(experiment_id: str, body: dict[str, Any], request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    exp = _experiments.get(_k(tenant_id, experiment_id))
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    winner = str(body.get("model_id", ""))
    if not winner:
        raise HTTPException(status_code=400, detail="model_id required")
    exp = {**exp, "winner": winner, "status": "completed"}
    _experiments[_k(tenant_id, experiment_id)] = exp
    return exp


@router.post("/synthetic/seed", status_code=201)
async def seed_synthetic(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # Seed some demo connectors and models for this tenant
    for ct, name in [("salesforce", "Salesforce CRM"), ("slack", "Slack Workspace"), ("github", "GitHub Enterprise")]:
        cid = f"conn-{uuid.uuid4().hex[:8]}"
        _connectors[_k(tenant_id, cid)] = {
            "id": cid, "tenant_id": tenant_id, "connector_type": ct, "name": name,
            "description": f"Synthetic {name} connector", "credential_ref": "vault://synthetic/demo",
            "status": "registered", "health_status": "healthy", "created_at": _now(), "mode": "synthetic",
        }
    for prov, model in [("openai", "gpt-4o"), ("anthropic", "claude-3.5-sonnet")]:
        mid = f"model-{uuid.uuid4().hex[:8]}"
        _models[_k(tenant_id, mid)] = {
            "id": mid, "tenant_id": tenant_id, "provider": prov, "model_name": model,
            "version": "1.0", "capabilities": ["chat", "function_calling"],
            "context_limit": 128000, "cost_per_1k_tokens": 0.005, "quality_score": 0.9,
            "availability": 0.99, "privacy_level": "private", "locality": "cloud",
            "supported_tools": ["function_calling"], "supported_modalities": ["text"],
            "status": "active", "created_at": _now(),
        }
    return {"seeded": True, "tenant_id": tenant_id, "connectors": 3, "models": 2}


@router.get("/synthetic/data")
async def get_synthetic_data(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "connectors": _list_for_tenant(_connectors, tenant_id),
        "models": _list_for_tenant(_models, tenant_id),
        "health": _list_for_tenant(_health, tenant_id),
    }
