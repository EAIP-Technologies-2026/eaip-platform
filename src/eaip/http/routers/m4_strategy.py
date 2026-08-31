from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/m4", tags=["m4"])

# ── in-memory stores (tenant-scoped) ─────────────────────────────────
_objectives: dict[str, dict[str, Any]] = {}
_initiatives: dict[str, dict[str, Any]] = {}
_constraints: dict[str, dict[str, Any]] = {}
_themes: dict[str, dict[str, Any]] = {}
_states: dict[str, list[dict[str, Any]]] = {}
_graph_edges: dict[str, list[dict[str, Any]]] = {}
_cycles: dict[str, dict[str, Any]] = {}
_gov_policies: dict[str, dict[str, Any]] = {}
_gov_decisions: dict[str, list[dict[str, Any]]] = {}


def _k(tenant_id: str, entity_id: str) -> str:
    return f"{tenant_id}:{entity_id}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ── helpers for tenant filtering ──────────────────────────────────────
def _list_for_tenant(store: dict[str, Any], tenant_id: str) -> list[dict[str, Any]]:
    prefix = f"{tenant_id}:"
    return [v for k, v in store.items() if k.startswith(prefix)]


# ── Objectives ────────────────────────────────────────────────────────
@router.post("/objectives", status_code=201)
async def create_objective(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    title = str(body.get("title", "")).strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    obj_id = f"obj-{uuid.uuid4().hex[:8]}"
    rec: dict[str, Any] = {
        "id": obj_id,
        "tenant_id": tenant_id,
        "title": title,
        "description": str(body.get("description", "")),
        "priority": str(body.get("priority", "medium")),
        "owner": str(body.get("owner", "")),
        "time_horizon": str(body.get("time_horizon", "annual")),
        "status": "draft",
        "created_at": _now(),
        "supersedes": None,
    }
    _objectives[_k(tenant_id, obj_id)] = rec
    return rec


@router.get("/objectives")
async def list_objectives(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_objectives, tenant_id)


@router.get("/objectives/{obj_id}")
async def get_objective(obj_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _objectives.get(_k(tenant_id, obj_id))
    if not rec:
        raise HTTPException(status_code=404, detail="objective not found")
    return rec


@router.patch("/objectives/{obj_id}")
async def update_objective(obj_id: str, request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, obj_id)
    rec = _objectives.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="objective not found")
    allowed = {"title", "description", "priority", "owner", "time_horizon", "status"}
    updated = dict(rec)
    for k, v in body.items():
        if k in allowed:
            updated[k] = v
    updated["updated_at"] = _now()
    _objectives[key] = updated
    return updated


@router.post("/objectives/{obj_id}/supersede", status_code=201)
async def supersede_objective(obj_id: str, request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, obj_id)
    old = _objectives.get(key)
    if not old:
        raise HTTPException(status_code=404, detail="objective not found")
    # mark old superseded
    old_updated = dict(old)
    old_updated["status"] = "superseded"
    _objectives[key] = old_updated
    new_title = str(body.get("new_title", body.get("title", ""))).strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="new_title required")
    new_id = f"obj-{uuid.uuid4().hex[:8]}"
    new_rec: dict[str, Any] = {
        "id": new_id,
        "tenant_id": tenant_id,
        "title": new_title,
        "description": str(body.get("new_description", body.get("description", ""))),
        "priority": str(body.get("priority", old.get("priority", "medium"))),
        "owner": str(body.get("owner", old.get("owner", ""))),
        "time_horizon": str(body.get("time_horizon", old.get("time_horizon", "annual"))),
        "status": "draft",
        "created_at": _now(),
        "supersedes": obj_id,
    }
    _objectives[_k(tenant_id, new_id)] = new_rec
    return new_rec


# ── Initiatives ───────────────────────────────────────────────────────
@router.post("/initiatives", status_code=201)
async def create_initiative(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    objective_id = str(body.get("objective_id", "")).strip()
    if not objective_id:
        raise HTTPException(status_code=400, detail="objective_id required")
    if _k(tenant_id, objective_id) not in _objectives:
        raise HTTPException(status_code=404, detail="objective not found")
    title = str(body.get("title", "")).strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    ini_id = f"ini-{uuid.uuid4().hex[:8]}"
    rec: dict[str, Any] = {
        "id": ini_id,
        "tenant_id": tenant_id,
        "objective_id": objective_id,
        "title": title,
        "description": str(body.get("description", "")),
        "budget": float(body.get("budget", 0) or 0),
        "owner": str(body.get("owner", "")),
        "status": "planned",
        "created_at": _now(),
    }
    _initiatives[_k(tenant_id, ini_id)] = rec
    return rec


@router.get("/initiatives")
async def list_initiatives(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), objective_id: str = "") -> list[dict[str, Any]]:
    items = _list_for_tenant(_initiatives, tenant_id)
    if objective_id:
        items = [i for i in items if i.get("objective_id") == objective_id]
    return items


@router.get("/initiatives/{ini_id}")
async def get_initiative(ini_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _initiatives.get(_k(tenant_id, ini_id))
    if not rec:
        raise HTTPException(status_code=404, detail="initiative not found")
    return rec


# ── Constraints ───────────────────────────────────────────────────────
@router.post("/constraints", status_code=201)
async def create_constraint(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    con_id = f"con-{uuid.uuid4().hex[:8]}"
    rec: dict[str, Any] = {
        "id": con_id,
        "tenant_id": tenant_id,
        "type": str(body.get("type", body.get("constraint_type", "generic"))),
        "description": str(body.get("description", "")),
        "severity": str(body.get("severity", "medium")),
        "created_at": _now(),
    }
    _constraints[_k(tenant_id, con_id)] = rec
    return rec


@router.get("/constraints")
async def list_constraints(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_constraints, tenant_id)


# ── Themes ────────────────────────────────────────────────────────────
@router.post("/themes", status_code=201)
async def create_theme(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    thm_id = f"thm-{uuid.uuid4().hex[:8]}"
    rec: dict[str, Any] = {
        "id": thm_id,
        "tenant_id": tenant_id,
        "name": name,
        "description": str(body.get("description", "")),
        "weight": float(body.get("weight", 1.0) or 1.0),
        "created_at": _now(),
    }
    _themes[_k(tenant_id, thm_id)] = rec
    return rec


@router.get("/themes")
async def list_themes(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_themes, tenant_id)


# ── State snapshots ───────────────────────────────────────────────────
@router.post("/state/snapshot", status_code=201)
async def create_snapshot(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    history = _states.get(tenant_id, [])
    version = (history[-1]["version"] + 1) if history else 1
    state_id = f"state-{uuid.uuid4().hex[:8]}"
    # snapshot objectives
    objs = _list_for_tenant(_objectives, tenant_id)
    rec: dict[str, Any] = {
        "id": state_id,
        "tenant_id": tenant_id,
        "version": version,
        "objectives_snapshot": objs,
        "rationale": str(body.get("rationale", "")),
        "approval": str(body.get("approval", "")),
        "created_at": _now(),
        "supersedes": history[-1]["id"] if history else None,
    }
    _states.setdefault(tenant_id, []).append(rec)
    return rec


@router.get("/state/current")
async def get_current_state(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    history = _states.get(tenant_id, [])
    if not history:
        raise HTTPException(status_code=404, detail="no state")
    return history[-1]


@router.get("/state/history")
async def get_state_history(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _states.get(tenant_id, [])


# ── Graph ─────────────────────────────────────────────────────────────
@router.post("/graph/connect", status_code=201)
async def graph_connect(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from_type = str(body.get("from_type", ""))
    from_id = str(body.get("from_id", ""))
    to_type = str(body.get("to_type", ""))
    to_id = str(body.get("to_id", ""))
    if not all([from_type, from_id, to_type, to_id]):
        raise HTTPException(status_code=400, detail="from_type, from_id, to_type, to_id required")
    edge: dict[str, Any] = {
        "id": f"edge-{uuid.uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "from_type": from_type,
        "from_id": from_id,
        "to_type": to_type,
        "to_id": to_id,
        "created_at": _now(),
    }
    _graph_edges.setdefault(tenant_id, []).append(edge)
    return edge


@router.get("/graph")
async def get_graph(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    for o in _list_for_tenant(_objectives, tenant_id):
        nodes.append({"type": "objective", "id": o["id"], "title": o["title"]})
    for i in _list_for_tenant(_initiatives, tenant_id):
        nodes.append({"type": "initiative", "id": i["id"], "title": i["title"]})
    for t in _list_for_tenant(_themes, tenant_id):
        nodes.append({"type": "theme", "id": t["id"], "title": t["name"]})
    edges = _graph_edges.get(tenant_id, [])
    return {"nodes": nodes, "edges": edges, "tenant_id": tenant_id}


@router.get("/graph/trace/{objective_id}")
async def trace_objective(objective_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    obj = _objectives.get(_k(tenant_id, objective_id))
    if not obj:
        raise HTTPException(status_code=404, detail="objective not found")
    # simple trace: find initiatives linked + edges traversing
    initiatives = [i for i in _list_for_tenant(_initiatives, tenant_id) if i.get("objective_id") == objective_id]
    edges = _graph_edges.get(tenant_id, [])
    related_edges = [e for e in edges if e.get("from_id") == objective_id or e.get("to_id") == objective_id]
    return {"objective": obj, "initiatives": initiatives, "edges": related_edges, "trace": [objective_id] + [i["id"] for i in initiatives]}


# ── Intelligence cycles ───────────────────────────────────────────────
@router.post("/cycles", status_code=201)
async def start_cycle(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    objective = str(body.get("objective", ""))
    if not objective:
        raise HTTPException(status_code=400, detail="objective required")
    cyc_id = f"ril-{uuid.uuid4().hex[:8]}"
    rec: dict[str, Any] = {
        "id": cyc_id,
        "tenant_id": tenant_id,
        "objective": objective,
        "context": body.get("context") or {},
        "observations": [],
        "reasoning": {},
        "plan": {},
        "actions": [],
        "measurements": [],
        "reflection": {},
        "correction": {},
        "status": "started",
        "created_at": _now(),
    }
    _cycles[_k(tenant_id, cyc_id)] = rec
    return rec


@router.get("/cycles")
async def list_cycles(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_cycles, tenant_id)


@router.get("/cycles/{cyc_id}")
async def get_cycle(cyc_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _cycles.get(_k(tenant_id, cyc_id))
    if not rec:
        raise HTTPException(status_code=404, detail="cycle not found")
    return rec


@router.post("/cycles/{cyc_id}/observe")
async def cycle_observe(cyc_id: str, request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _cycles.get(_k(tenant_id, cyc_id))
    if not rec:
        raise HTTPException(status_code=404, detail="cycle not found")
    observations = body.get("observations") or []
    if not isinstance(observations, list):
        observations = [observations]
    rec["observations"] = observations
    rec["status"] = "observed"
    _cycles[_k(tenant_id, cyc_id)] = rec
    return rec


@router.post("/cycles/{cyc_id}/reason")
async def cycle_reason(cyc_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _cycles.get(_k(tenant_id, cyc_id))
    if not rec:
        raise HTTPException(status_code=404, detail="cycle not found")
    reasoning = {"direct": True, "objective": rec["objective"], "observations": len(rec.get("observations", [])), "confidence": 0.7, "created_at": _now()}
    rec["reasoning"] = reasoning
    rec["status"] = "reasoned"
    _cycles[_k(tenant_id, cyc_id)] = rec
    return reasoning


@router.post("/cycles/{cyc_id}/plan")
async def cycle_plan(cyc_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _cycles.get(_k(tenant_id, cyc_id))
    if not rec:
        raise HTTPException(status_code=404, detail="cycle not found")
    plan = {"plan_id": f"plan-{uuid.uuid4().hex[:6]}", "objective": rec["objective"], "reasoning": rec.get("reasoning", {}), "created_at": _now()}
    rec["plan"] = plan
    rec["status"] = "planned"
    _cycles[_k(tenant_id, cyc_id)] = rec
    return plan


@router.post("/cycles/{cyc_id}/execute")
async def cycle_execute(cyc_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _cycles.get(_k(tenant_id, cyc_id))
    if not rec:
        raise HTTPException(status_code=404, detail="cycle not found")
    action = {"type": "execute", "plan": rec.get("plan", {}), "executed_at": _now()}
    rec["actions"] = [action]
    rec["status"] = "executed"
    _cycles[_k(tenant_id, cyc_id)] = rec
    return {"status": "executed", "actions": len(rec["actions"])}


@router.post("/cycles/{cyc_id}/measure")
async def cycle_measure(cyc_id: str, request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _cycles.get(_k(tenant_id, cyc_id))
    if not rec:
        raise HTTPException(status_code=404, detail="cycle not found")
    measurements = body.get("measurements") or []
    if not isinstance(measurements, list):
        measurements = [measurements]
    if not measurements:
        measurements = [{"source": "direct", "actions_measured": len(rec.get("actions", []))}]
    rec["measurements"] = measurements
    rec["status"] = "measured"
    _cycles[_k(tenant_id, cyc_id)] = rec
    return {"measurements": measurements}


@router.post("/cycles/{cyc_id}/reflect")
async def cycle_reflect(cyc_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _cycles.get(_k(tenant_id, cyc_id))
    if not rec:
        raise HTTPException(status_code=404, detail="cycle not found")
    pred = rec.get("reasoning", {}).get("confidence", 0.5)
    actual_success = sum(1 for m in rec.get("measurements", []) if isinstance(m, dict) and m.get("status") == "met")
    total = len(rec.get("measurements", [])) or 1
    rate = actual_success / total
    gap = abs(pred - rate)
    reflection = {"predicted_confidence": pred, "actual_success_rate": round(rate, 3), "gap": round(gap, 3), "calibration": "well_calibrated" if gap < 0.2 else "over_confident" if pred > rate else "under_confident", "created_at": _now()}
    rec["reflection"] = reflection
    rec["status"] = "reflected"
    _cycles[_k(tenant_id, cyc_id)] = rec
    return reflection


@router.post("/cycles/{cyc_id}/correct")
async def cycle_correct(cyc_id: str, request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _cycles.get(_k(tenant_id, cyc_id))
    if not rec:
        raise HTTPException(status_code=404, detail="cycle not found")
    correction_input = str(body.get("correction", body.get("reason", "")))
    calibration = rec.get("reflection", {}).get("calibration", "unknown")
    adjustments: list[str] = []
    if calibration == "over_confident":
        adjustments = ["reduce_confidence_threshold", "require_more_evidence"]
    elif calibration == "under_confident":
        adjustments = ["increase_exploration", "lower_evidence_threshold"]
    else:
        adjustments = ["maintain_current_strategy"]
    if correction_input:
        adjustments.append(correction_input)
    correction = {"calibration": calibration, "adjustments": adjustments, "objective": rec["objective"], "created_at": _now()}
    rec["correction"] = correction
    rec["status"] = "corrected"
    _cycles[_k(tenant_id, cyc_id)] = rec
    return correction


# ── Governance (M4) ───────────────────────────────────────────────────
@router.post("/governance/policies", status_code=201)
async def create_gov_policy(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    pid = f"pol-{uuid.uuid4().hex[:8]}"
    rec: dict[str, Any] = {
        "id": pid,
        "tenant_id": tenant_id,
        "name": name,
        "conditions": body.get("conditions") or {},
        "effect": str(body.get("effect", "allow")),
        "priority": int(body.get("priority", 0) or 0),
        "created_at": _now(),
    }
    _gov_policies[_k(tenant_id, pid)] = rec
    return rec


@router.get("/governance/policies")
async def list_gov_policies(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_gov_policies, tenant_id)


@router.post("/governance/evaluate")
async def evaluate_governance(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    who = str(body.get("who", ""))
    what = str(body.get("what", body.get("action", "")))
    decision = "ALLOW"
    reason = "all checks passed"
    # simple policy check: if any policy has deny effect and matches risk_level high
    risk = str(body.get("risk_level", body.get("risk", "low")))
    if risk == "high" or risk == "critical":
        policies = _list_for_tenant(_gov_policies, tenant_id)
        for p in sorted(policies, key=lambda x: x.get("priority", 0), reverse=True):
            if p.get("effect") == "deny":
                decision = "DENY"
                reason = f"policy '{p['name']}' denies high risk"
                break
            if p.get("effect") == "approval" and decision == "ALLOW":
                decision = "APPROVAL"
                reason = f"policy '{p['name']}' requires approval"
    rec: dict[str, Any] = {
        "id": f"gov-{uuid.uuid4().hex[:8]}",
        "tenant_id": tenant_id,
        "who": who,
        "what": what,
        "why": str(body.get("why", "")),
        "risk_level": risk,
        "autonomy_level": str(body.get("autonomy_level", "L2")),
        "cost_estimate": float(body.get("cost_estimate", 0) or 0),
        "decision": decision,
        "reason": reason,
        "created_at": _now(),
    }
    _gov_decisions.setdefault(tenant_id, []).append(rec)
    return rec


@router.get("/governance/decisions")
async def list_gov_decisions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _gov_decisions.get(tenant_id, [])


# ── KCR ───────────────────────────────────────────────────────────────
@router.post("/kcr/assemble")
async def kcr_assemble(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    query = str(body.get("query", "")).strip()
    if not query:
        raise HTTPException(status_code=400, detail="query required")
    max_tokens = int(body.get("max_tokens", 4000) or 4000)
    include_strategy = bool(body.get("include_strategy", True))
    include_temporal = bool(body.get("include_temporal", False))
    # try using KCRService
    try:
        from eaip.knowledge.kcr import KCRService
        svc = KCRService()
        # try strategic context if requested
        if include_strategy or include_temporal:
            # synthesize without engine – use stored objectives
            parts: list[dict[str, Any]] = []
            if include_strategy:
                for o in _list_for_tenant(_objectives, tenant_id)[:10]:
                    parts.append({"source": "strategic_objective", "content": f"Objective: {o['title']} | Status: {o.get('status')} | Priority: {o.get('priority')}", "entity_id": o["id"], "tenant_id": tenant_id})
            if include_temporal:
                for st in (_states.get(tenant_id, [])[-5:]):
                    parts.append({"source": "temporal_state", "content": f"State v{st['version']}: {len(st.get('objectives_snapshot', []))} objectives", "entity_id": st["id"], "tenant_id": tenant_id})
            # also call base assemble
            base = await svc.assemble(tenant_id=tenant_id, query=query, max_tokens=max_tokens)
            # merge
            all_parts = base.get("parts", []) + parts
            return {"tenant_id": tenant_id, "query": query, "parts": all_parts, "bounded": True, "total_chars": sum(len(p.get("content", "")) for p in all_parts), "count": len(all_parts)}
        else:
            return await svc.assemble(tenant_id=tenant_id, query=query, max_tokens=max_tokens)
    except Exception:
        # fallback synthetic
        parts = [{"source": "knowledge", "content": f"Context for '{query}'", "tenant_id": tenant_id}]
        if include_strategy:
            for o in _list_for_tenant(_objectives, tenant_id)[:5]:
                parts.append({"source": "strategic_objective", "content": o["title"], "entity_id": o["id"]})
        return {"tenant_id": tenant_id, "query": query, "parts": parts, "bounded": True, "total_chars": sum(len(p.get("content", "")) for p in parts), "count": len(parts)}


@router.get("/kcr/context/{query}")
async def kcr_context(query: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # test helper – assemble with defaults
    from eaip.knowledge.kcr import KCRService
    svc = KCRService()
    try:
        return await svc.assemble(tenant_id=tenant_id, query=query, max_tokens=4000)
    except Exception:
        return {"tenant_id": tenant_id, "query": query, "parts": [{"source": "knowledge", "content": f"Context for '{query}'", "tenant_id": tenant_id}], "bounded": True, "total_chars": len(query), "count": 1}


# ── Synthetic seed ────────────────────────────────────────────────────
@router.post("/synthetic/seed", status_code=201)
async def synthetic_seed(request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # create synthetic objectives, initiatives, themes, state, policy, cycle
    o1 = await create_objective(request, {"title": "Synthetic Objective 1", "description": "Seeded", "priority": "high", "owner": "system", "time_horizon": "annual"}, tenant_id, _user)
    o2 = await create_objective(request, {"title": "Synthetic Objective 2", "description": "Seeded", "priority": "medium", "owner": "system"}, tenant_id, _user)
    await create_initiative(request, {"objective_id": o1["id"], "title": "Seed Initiative", "description": "Seeded initiative", "budget": 10000, "owner": "system"}, tenant_id, _user)
    await create_constraint(request, {"type": "budget", "description": "Synthetic constraint", "severity": "medium"}, tenant_id, _user)
    await create_theme(request, {"name": "Growth", "description": "Synthetic theme", "weight": 0.8}, tenant_id, _user)
    await create_snapshot(request, {"rationale": "Synthetic seed snapshot"}, tenant_id, _user)
    await create_gov_policy(request, {"name": "Synthetic Policy", "conditions": {}, "effect": "allow", "priority": 1}, tenant_id, _user)
    await start_cycle(request, {"objective": "Synthetic cycle", "context": {"seed": True}}, tenant_id, _user)
    return {"tenant_id": tenant_id, "seeded": True, "objectives": [o1["id"], o2["id"]]}
