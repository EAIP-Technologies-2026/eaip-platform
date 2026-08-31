from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/m5", tags=["m5"])

# ── stores ─────────────────────────────────────────────────────────────
_learning_records: dict[str, dict[str, Any]] = {}
_lessons: dict[str, dict[str, Any]] = {}
_feedback: dict[str, list[dict[str, Any]]] = {}
_adaptations: dict[str, dict[str, Any]] = {}
_proofs: dict[str, dict[str, Any]] = {}
_proofs_by_execution: dict[str, list[str]] = {}
_proofs_by_tenant: dict[str, list[str]] = {}
_policies: dict[str, dict[str, Any]] = {}
_decisions: dict[str, list[dict[str, Any]]] = {}
_exceptions: dict[str, list[dict[str, Any]]] = {}
_violations: dict[str, list[dict[str, Any]]] = {}
_approvals: dict[str, dict[str, Any]] = {}


def _k(tenant_id: str, entity_id: str) -> str:
    return f"{tenant_id}:{entity_id}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _list_for_tenant(store: dict[str, Any], tenant_id: str) -> list[dict[str, Any]]:
    prefix = f"{tenant_id}:"
    return [v for k, v in store.items() if k.startswith(prefix)]


# ── Learning: observe ─────────────────────────────────────────────────
@router.post("/learning/observe", status_code=201)
async def observe_learning(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    source_type = str(body.get("source_type", "generic"))
    source_id = str(body.get("source_id", f"src-{uuid.uuid4().hex[:6]}"))
    observation = body.get("observation") or {}
    rec_id = f"lr-{uuid.uuid4().hex[:10]}"
    rec: dict[str, Any] = {
        "id": rec_id,
        "tenant_id": tenant_id,
        "source_type": source_type,
        "source_id": source_id,
        "observation": observation,
        "confidence": 0.0,
        "status": "proposed",
        "created_at": _now(),
    }
    _learning_records[_k(tenant_id, rec_id)] = rec
    return rec


@router.get("/learning/records")
async def list_learning_records(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_learning_records, tenant_id)


@router.get("/learning/records/{rec_id}")
async def get_learning_record(rec_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _learning_records.get(_k(tenant_id, rec_id))
    if not rec:
        raise HTTPException(status_code=404, detail="learning record not found")
    return rec


@router.post("/learning/records/{rec_id}/evaluate")
async def evaluate_record(rec_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, rec_id)
    rec = _learning_records.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="learning record not found")
    obs = rec.get("observation", {})
    significance = "high" if obs.get("error") or obs.get("failure") else "medium" if obs.get("success") else "low"
    updated = dict(rec)
    updated["evaluation"] = {"significance": significance, "evaluated_at": _now()}
    updated["confidence"] = min(float(rec.get("confidence", 0)) + 0.2, 1.0)
    updated["status"] = "validating"
    _learning_records[key] = updated
    return updated


# ── Lessons ───────────────────────────────────────────────────────────
@router.post("/learning/lessons", status_code=201)
async def propose_lesson(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    lr_id = str(body.get("learning_record_id", "")).strip()
    if not lr_id:
        raise HTTPException(status_code=400, detail="learning_record_id required")
    if _k(tenant_id, lr_id) not in _learning_records:
        raise HTTPException(status_code=404, detail="learning record not found")
    title = str(body.get("title", "")).strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    les_id = f"les-{uuid.uuid4().hex[:10]}"
    rec: dict[str, Any] = {
        "id": les_id,
        "tenant_id": tenant_id,
        "learning_record_id": lr_id,
        "title": title,
        "description": str(body.get("description", "")),
        "evidence": body.get("evidence") or [],
        "confidence": float(body.get("confidence", 0.5) or 0.5),
        "status": "proposed",
        "created_at": _now(),
    }
    _lessons[_k(tenant_id, les_id)] = rec
    # update learning record
    lr_key = _k(tenant_id, lr_id)
    lr = _learning_records[lr_key]
    _learning_records[lr_key] = dict(lr, proposed_lesson=les_id)
    return rec


@router.get("/learning/lessons")
async def list_lessons(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_lessons, tenant_id)


@router.get("/learning/lessons/{les_id}")
async def get_lesson(les_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _lessons.get(_k(tenant_id, les_id))
    if not rec:
        raise HTTPException(status_code=404, detail="lesson not found")
    return rec


@router.post("/learning/lessons/{les_id}/approve")
async def approve_lesson(les_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, les_id)
    rec = _lessons.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="lesson not found")
    updated = dict(rec)
    updated["status"] = "approved"
    updated["approval_id"] = f"appr-{uuid.uuid4().hex[:8]}"
    updated["approved_at"] = _now()
    _lessons[key] = updated
    return updated


@router.post("/learning/lessons/{les_id}/reject")
async def reject_lesson(les_id: str, request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, les_id)
    rec = _lessons.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="lesson not found")
    updated = dict(rec)
    updated["status"] = "rejected"
    updated["rejection_reason"] = str(body.get("reason", ""))
    updated["rejected_at"] = _now()
    _lessons[key] = updated
    return updated


@router.post("/learning/lessons/{les_id}/activate")
async def activate_lesson(les_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, les_id)
    rec = _lessons.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="lesson not found")
    if rec.get("status") not in ("approved", "validating", "proposed"):
        raise HTTPException(status_code=400, detail=f"cannot activate from status {rec.get('status')}")
    updated = dict(rec)
    updated["status"] = "activated"
    updated["effective_date"] = _now()
    _lessons[key] = updated
    return updated


@router.post("/learning/lessons/{les_id}/supersede", status_code=201)
async def supersede_lesson(les_id: str, request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, les_id)
    rec = _lessons.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="lesson not found")
    new_data = body.get("new_lesson_data") or body
    # create new lesson
    new_id = f"les-{uuid.uuid4().hex[:10]}"
    new_rec: dict[str, Any] = {
        "id": new_id,
        "tenant_id": tenant_id,
        "learning_record_id": rec.get("learning_record_id", ""),
        "title": str(new_data.get("title", rec.get("title", "") + " v2")),
        "description": str(new_data.get("description", rec.get("description", ""))),
        "evidence": new_data.get("evidence") or rec.get("evidence", []),
        "confidence": float(new_data.get("confidence", rec.get("confidence", 0.5)) or 0.5),
        "status": "proposed",
        "supersedes": les_id,
        "created_at": _now(),
    }
    _lessons[_k(tenant_id, new_id)] = new_rec
    # mark old superseded
    updated = dict(rec)
    updated["status"] = "superseded"
    updated["superseded_by"] = new_id
    _lessons[key] = updated
    return new_rec


# ── Feedback ──────────────────────────────────────────────────────────
def _add_feedback(tenant_id: str, kind: str, data: dict[str, Any]) -> dict[str, Any]:
    entry = {"kind": kind, "tenant_id": tenant_id, **data, "created_at": _now()}
    _feedback.setdefault(tenant_id, []).append(entry)
    return entry


@router.post("/learning/feedback/prediction", status_code=201)
async def feedback_prediction(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _add_feedback(tenant_id, "prediction", {"prediction_id": str(body.get("prediction_id", "")), "actual_outcome": body.get("actual_outcome")})


@router.post("/learning/feedback/decision", status_code=201)
async def feedback_decision(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _add_feedback(tenant_id, "decision", {"decision_id": str(body.get("decision_id", "")), "actual_outcome": body.get("actual_outcome")})


@router.post("/learning/feedback/workflow", status_code=201)
async def feedback_workflow(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _add_feedback(tenant_id, "workflow", {"workflow_id": str(body.get("workflow_id", "")), "success": bool(body.get("success", True)), "details": body.get("details") or {}})


@router.post("/learning/feedback/agent", status_code=201)
async def feedback_agent(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _add_feedback(tenant_id, "agent", {"agent_id": str(body.get("agent_id", "")), "metrics": body.get("metrics") or {}})


@router.get("/learning/feedback/summary")
async def feedback_summary(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    entries = _feedback.get(tenant_id, [])
    by_kind: dict[str, int] = {}
    for e in entries:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
    return {"tenant_id": tenant_id, "total": len(entries), "by_kind": by_kind, "entries": entries[-20:]}


# ── Adaptations ───────────────────────────────────────────────────────
@router.post("/learning/adaptations", status_code=201)
async def propose_adaptation(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    lesson_id = str(body.get("lesson_id", "")).strip()
    if not lesson_id:
        raise HTTPException(status_code=400, detail="lesson_id required")
    ad_id = f"adp-{uuid.uuid4().hex[:10]}"
    rec: dict[str, Any] = {
        "id": ad_id,
        "tenant_id": tenant_id,
        "lesson_id": lesson_id,
        "target_type": str(body.get("target_type", "")),
        "target_id": str(body.get("target_id", "")),
        "proposed_change": body.get("proposed_change") or {},
        "risk_level": str(body.get("risk_level", "low")),
        "status": "proposed",
        "created_at": _now(),
    }
    _adaptations[_k(tenant_id, ad_id)] = rec
    return rec


@router.get("/learning/adaptations")
async def list_adaptations(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_adaptations, tenant_id)


# ── Audit proofs ──────────────────────────────────────────────────────
@router.post("/audit/proofs", status_code=201)
async def generate_proof(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    import hashlib, json
    execution_id = str(body.get("execution_id", f"exec-{uuid.uuid4().hex[:8]}"))
    proof_id = f"proof-{uuid.uuid4().hex[:12]}"
    ts = _now()
    # previous hash from tenant proofs
    prev_list = _proofs_by_tenant.get(tenant_id, [])
    prev_hash = _proofs[prev_list[-1]]["current_hash"] if prev_list else ""
    chain_index = len(prev_list)

    def _h(data: Any) -> str:
        return hashlib.sha256(json.dumps(data or {}, sort_keys=True).encode()).hexdigest()

    intent_hash = _h(body.get("intent"))
    context_hash = _h(body.get("context"))
    policy_hash = _h(body.get("policy"))
    model_hash = _h(body.get("model"))
    tool_hash = _h(body.get("tool"))
    connector_hash = _h(body.get("connector"))
    input_hash = _h(body.get("input_data") or body.get("inputs"))
    output_hash = _h(body.get("output_data") or body.get("outputs"))
    current_hash = hashlib.sha256(f"{proof_id}|{tenant_id}|{execution_id}|{intent_hash}|{context_hash}|{policy_hash}|{model_hash}|{tool_hash}|{connector_hash}|{input_hash}|{output_hash}|{ts}|{prev_hash}|{chain_index}".encode()).hexdigest()

    rec: dict[str, Any] = {
        "proof_id": proof_id,
        "tenant_id": tenant_id,
        "execution_id": execution_id,
        "intent_hash": intent_hash,
        "context_hash": context_hash,
        "policy_hash": policy_hash,
        "model_hash": model_hash,
        "tool_hash": tool_hash,
        "connector_hash": connector_hash,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "timestamp": ts,
        "previous_hash": prev_hash,
        "current_hash": current_hash,
        "chain_index": chain_index,
    }
    _proofs[proof_id] = rec
    _proofs_by_execution.setdefault(f"{tenant_id}:{execution_id}", []).append(proof_id)
    _proofs_by_tenant.setdefault(tenant_id, []).append(proof_id)
    return rec


@router.get("/audit/proofs/{proof_id}")
async def get_proof(proof_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _proofs.get(proof_id)
    if not rec or rec.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="proof not found")
    return rec


@router.get("/audit/proofs")
async def list_proofs(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    ids = _proofs_by_tenant.get(tenant_id, [])
    return [_proofs[pid] for pid in ids]


@router.post("/audit/proofs/{proof_id}/verify")
async def verify_proof(proof_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _proofs.get(proof_id)
    if not rec or rec.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="proof not found")
    import hashlib
    expected = hashlib.sha256(f"{rec['proof_id']}|{rec['tenant_id']}|{rec['execution_id']}|{rec['intent_hash']}|{rec['context_hash']}|{rec['policy_hash']}|{rec['model_hash']}|{rec['tool_hash']}|{rec['connector_hash']}|{rec['input_hash']}|{rec['output_hash']}|{rec['timestamp']}|{rec['previous_hash']}|{rec['chain_index']}".encode()).hexdigest()
    valid = rec["current_hash"] == expected
    return {"proof_id": proof_id, "valid": valid, "details": {"expected_hash": expected, "actual_hash": rec["current_hash"]}}


@router.post("/audit/chain/verify")
async def verify_chain(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ids = _proofs_by_tenant.get(tenant_id, [])
    if not ids:
        return {"valid": True, "count": 0}
    for i, pid in enumerate(ids):
        rec = _proofs[pid]
        expected_prev = _proofs[ids[i - 1]]["current_hash"] if i > 0 else ""
        if rec["previous_hash"] != expected_prev:
            return {"valid": False, "count": len(ids), "broken_at": pid}
        # verify hash
        import hashlib
        expected = hashlib.sha256(f"{rec['proof_id']}|{rec['tenant_id']}|{rec['execution_id']}|{rec['intent_hash']}|{rec['context_hash']}|{rec['policy_hash']}|{rec['model_hash']}|{rec['tool_hash']}|{rec['connector_hash']}|{rec['input_hash']}|{rec['output_hash']}|{rec['timestamp']}|{rec['previous_hash']}|{rec['chain_index']}".encode()).hexdigest()
        if rec["current_hash"] != expected:
            return {"valid": False, "count": len(ids), "tampered_at": pid}
    return {"valid": True, "count": len(ids)}


@router.get("/audit/executions/{exec_id}/inspect")
async def inspect_execution(exec_id: str, request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = f"{tenant_id}:{exec_id}"
    pids = _proofs_by_execution.get(key, [])
    proofs = [_proofs[pid] for pid in pids]
    if not proofs:
        return {"execution_id": exec_id, "proofs": [], "count": 0}
    return {"execution_id": exec_id, "count": len(proofs), "proofs": proofs}


@router.post("/audit/replay/{execution_id}")
async def replay_execution(execution_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    safe_mode = bool((body or {}).get("safe_mode", True))
    key = f"{tenant_id}:{execution_id}"
    pids = _proofs_by_execution.get(key, [])
    proofs = [_proofs[pid] for pid in pids]
    steps: list[dict[str, Any]] = []
    for i, p in enumerate(proofs):
        steps.append({"step_id": f"step-{i}", "step_type": "proof_verification", "description": f"Verifying proof {p['proof_id']}", "proof_id": p["proof_id"], "simulated": True, "timestamp": _now()})
    # chain verification step
    ids = _proofs_by_tenant.get(tenant_id, [])
    chain_valid = True
    if ids:
        chain_valid = all(_proofs[ids[i]]["previous_hash"] == (_proofs[ids[i-1]]["current_hash"] if i>0 else "") for i in range(len(ids)))
    steps.append({"step_id": f"step-{len(steps)}", "step_type": "chain_verification", "description": "Full chain integrity verification", "simulated": True, "timestamp": _now(), "details": {"chain_valid": chain_valid}})
    return {"replay_id": f"replay-{uuid.uuid4().hex[:10]}", "execution_id": execution_id, "steps": steps, "success": chain_valid, "mode": "simulated" if safe_mode else "simulated", "idempotency_key": f"replay:{tenant_id}:{execution_id}"}


@router.get("/audit/verification/report")
async def verification_report(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ids = _proofs_by_tenant.get(tenant_id, [])
    valid = True
    if ids:
        import hashlib
        for i, pid in enumerate(ids):
            rec = _proofs[pid]
            expected_prev = _proofs[ids[i-1]]["current_hash"] if i>0 else ""
            if rec["previous_hash"] != expected_prev:
                valid = False
                break
            expected = hashlib.sha256(f"{rec['proof_id']}|{rec['tenant_id']}|{rec['execution_id']}|{rec['intent_hash']}|{rec['context_hash']}|{rec['policy_hash']}|{rec['model_hash']}|{rec['tool_hash']}|{rec['connector_hash']}|{rec['input_hash']}|{rec['output_hash']}|{rec['timestamp']}|{rec['previous_hash']}|{rec['chain_index']}".encode()).hexdigest()
            if rec["current_hash"] != expected:
                valid = False
                break
    return {"tenant_id": tenant_id, "valid": valid, "count": len(ids), "proofs": len(ids)}


# ── Governance (M5) ───────────────────────────────────────────────────
@router.post("/governance/policies", status_code=201)
async def create_m5_policy(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    pid = f"gp-{uuid.uuid4().hex[:10]}"
    rec: dict[str, Any] = {"id": pid, "tenant_id": tenant_id, "name": name, "conditions": body.get("conditions") or {}, "effect": str(body.get("effect", "allow")), "priority": int(body.get("priority", 0) or 0), "status": "active", "created_at": _now()}
    _policies[_k(tenant_id, pid)] = rec
    return rec


@router.get("/governance/policies")
async def list_m5_policies(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_policies, tenant_id)


@router.post("/governance/evaluate")
async def evaluate_m5_governance(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    who = str(body.get("who", ""))
    what = str(body.get("what", body.get("action", "")))
    risk = str(body.get("risk_level", "low"))
    # simple eval
    decision = "allow"
    reason = "all checks passed"
    policies = _list_for_tenant(_policies, tenant_id)
    for p in sorted(policies, key=lambda x: x.get("priority", 0), reverse=True):
        if p.get("effect") == "deny":
            decision = "deny"
            reason = f"policy '{p['name']}' denies"
            break
        if p.get("effect") == "approval" and decision == "allow":
            decision = "approval"
            reason = f"policy '{p['name']}' requires approval"
    rec: dict[str, Any] = {"id": f"gd-{uuid.uuid4().hex[:10]}", "tenant_id": tenant_id, "who": who, "what": what, "why": str(body.get("why", "")), "decision": decision, "reason": reason, "risk_level": risk, "created_at": _now()}
    _decisions.setdefault(tenant_id, []).append(rec)
    return rec


@router.get("/governance/decisions")
async def list_m5_decisions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _decisions.get(tenant_id, [])


@router.get("/governance/exceptions")
async def list_exceptions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _exceptions.get(tenant_id, [])


@router.get("/governance/violations")
async def list_violations(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _violations.get(tenant_id, [])


@router.get("/governance/metrics")
async def governance_metrics(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    policies = _list_for_tenant(_policies, tenant_id)
    return {"tenant_id": tenant_id, "total_policies": len(policies), "active_policies": sum(1 for p in policies if p.get("status") == "active"), "total_decisions": len(_decisions.get(tenant_id, [])), "total_exceptions": len(_exceptions.get(tenant_id, [])), "total_violations": len(_violations.get(tenant_id, []))}


# ── Approvals ─────────────────────────────────────────────────────────
@router.post("/approvals", status_code=201)
async def create_approval(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    target_type = str(body.get("target_type", "")).strip()
    if not target_type:
        raise HTTPException(status_code=400, detail="target_type required")
    ap_id = f"apr-{uuid.uuid4().hex[:10]}"
    rec: dict[str, Any] = {"id": ap_id, "tenant_id": tenant_id, "requester": _user.get("user_id", _user.get("sub", "user")), "target_type": target_type, "target_id": str(body.get("target_id", "")), "reason": str(body.get("reason", "")), "status": "pending", "created_at": _now()}
    _approvals[_k(tenant_id, ap_id)] = rec
    return rec


@router.get("/approvals")
async def list_approvals(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _list_for_tenant(_approvals, tenant_id)


@router.get("/approvals/pending")
async def list_pending_approvals(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [v for v in _list_for_tenant(_approvals, tenant_id) if v.get("status") == "pending"]


@router.post("/approvals/{ap_id}/approve")
async def approve_request(ap_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, ap_id)
    rec = _approvals.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="approval not found")
    if rec.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"already {rec.get('status')}")
    updated = dict(rec)
    updated["status"] = "approved"
    updated["approver"] = _user.get("user_id", _user.get("sub", "approver"))
    updated["decision_reason"] = str((body or {}).get("reason", ""))
    updated["decided_at"] = _now()
    _approvals[key] = updated
    return updated


@router.post("/approvals/{ap_id}/reject")
async def reject_request(ap_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, ap_id)
    rec = _approvals.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="approval not found")
    if rec.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"already {rec.get('status')}")
    updated = dict(rec)
    updated["status"] = "rejected"
    updated["approver"] = _user.get("user_id", _user.get("sub", "approver"))
    updated["decision_reason"] = str((body or {}).get("reason", ""))
    updated["decided_at"] = _now()
    _approvals[key] = updated
    return updated


@router.post("/approvals/{ap_id}/defer")
async def defer_request(ap_id: str, request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    key = _k(tenant_id, ap_id)
    rec = _approvals.get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="approval not found")
    if rec.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"already {rec.get('status')}")
    updated = dict(rec)
    updated["status"] = "deferred"
    updated["approver"] = _user.get("user_id", _user.get("sub", "approver"))
    updated["decision_reason"] = str((body or {}).get("reason", ""))
    updated["decided_at"] = _now()
    _approvals[key] = updated
    return updated


# ── Synthetic seed ────────────────────────────────────────────────────
@router.post("/synthetic/seed", status_code=201)
async def synthetic_seed_m5(request: Request, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # seed learning records, lessons, proofs, policies, approvals
    lr = await observe_learning(request, {"source_type": "synthetic", "source_id": "seed-1", "observation": {"success": True, "improvement": "seeded"}}, tenant_id, _user)
    ev = await evaluate_record(lr["id"], request, {}, tenant_id, _user)
    les = await propose_lesson(request, {"learning_record_id": lr["id"], "title": "Synthetic Lesson", "description": "Seeded lesson"}, tenant_id, _user)
    await approve_lesson(les["id"], request, {}, tenant_id, _user)
    await generate_proof(request, {"execution_id": f"exec-seed-{uuid.uuid4().hex[:6]}", "intent": {"seed": True}}, tenant_id, _user)
    await create_m5_policy(request, {"name": "Synthetic M5 Policy", "conditions": {}, "effect": "allow", "priority": 1}, tenant_id, _user)
    await create_approval(request, {"target_type": "lesson", "target_id": les["id"], "reason": "seeded"}, tenant_id, _user)
    _feedback.setdefault(tenant_id, []).append({"kind": "workflow", "workflow_id": "seed-wf", "success": True, "tenant_id": tenant_id, "created_at": _now()})
    return {"tenant_id": tenant_id, "seeded": True, "learning_record_id": lr["id"], "lesson_id": les["id"]}
