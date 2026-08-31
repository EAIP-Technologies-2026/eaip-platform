"""Enterprise Storyline + Decision Lineage + Explain This composition layer.

Composes REAL state from existing engines into business narratives:
- GET /api/storyline              -> reverse-chronological WHAT-CHANGED-TODAY feed
- GET /api/explain                -> contextual entity explanation
- GET /api/lineage/decision/{id}  -> SIGNAL .. AUDIT PROOF lineage

No new engines: reads M2 predictions/radar/briefings, approval center,
decision logs, audit chain, knowledge graph traversal.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(tags=["storyline"], dependencies=[Depends(get_current_user)])


def _parse_ts(value: Any) -> float:
    try:
        if isinstance(value, (int, float)):
            return float(value)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _accuracy_pct(pred: dict[str, Any]) -> float | None:
    acc = pred.get("accuracy")
    if acc is not None:
        try:
            return round(float(acc) * 100, 1)
        except Exception:
            return None
    err = pred.get("prediction_error")
    pv = pred.get("predicted_value")
    try:
        if err is not None and pv is not None and float(pv) != 0:
            return round(max(0.0, 1.0 - abs(float(err)) / abs(float(pv))) * 100, 1)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Storyline
# ---------------------------------------------------------------------------


@router.get("/storyline")
async def storyline(
    limit: int = Query(default=60, le=200),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    from eaip.http.routers import approval_center as _ac
    from eaip.http.routers import m2_intelligence as _m2

    await _m2.ensure_loaded()
    items: list[dict[str, Any]] = []

    # 1) Predictions + verified outcomes
    for p in _m2._predictions:
        if p.get("tenant_id") != tenant_id:
            continue
        acc = _accuracy_pct(p)
        has_actual = p.get("actual_outcome") is not None
        items.append({
            "id": f"pred-{p['prediction_id']}",
            "ts": p.get("created_at"),
            "source": "m2.prediction",
            "kind": "prediction",
            "signal": (
                f"Predicted {p.get('metric', p.get('target', 'metric'))} at "
                f"{p.get('predicted_value')} for {p.get('target_entity', 'entity')} ({p.get('horizon', '')})"
            ),
            "insight": "; ".join(p.get("evidence") or []) or "Model forecast from operational signals",
            "foresight": (p.get("business_impact") or ""),
            "action": (
                "EAIP monitored and prepared remediation options"
                if not has_actual else "EAIP recommended a plan which moved to execution"
            ),
            "governance": None,
            "outcome": (
                f"Actual {p.get('actual_outcome')} vs predicted {p.get('predicted_value')}"
                if has_actual else None
            ),
            "verification": (
                {"status": "verified" if (acc is not None and acc >= 85) else "evaluated",
                 "accuracy_pct": acc, "error": p.get("prediction_error")}
                if has_actual else {"status": "pending"}
            ),
            "refs": {"prediction_id": p["prediction_id"], "target_entity": p.get("target_entity")},
        })

    # 2) Risk radar entries
    for r in _m2._radar:
        if r.get("tenant_id") != tenant_id:
            continue
        factors = r.get("factors") or []
        items.append({
            "id": f"radar-{r['radar_id']}",
            "ts": r.get("created_at"),
            "source": "m2.radar",
            "kind": str(r.get("type", "risk")),
            "signal": r.get("title", ""),
            "insight": ("Driven by: " + ", ".join(factors)) if factors else "",
            "foresight": f"Score {float(r.get('score', 0)):.2f} — monitor or intervene.",
            "action": "Added to risk radar; EAIP evaluates mitigation options automatically",
            "governance": None,
            "outcome": None,
            "verification": {"status": "n/a"},
            "refs": {"radar_id": r["radar_id"]},
        })

    # 3) Approvals — governance-visible events
    for a in getattr(_ac, "_approvals", []):
        if a.get("tenant_id") != tenant_id:
            continue
        status_ = a.get("status", "pending")
        meta = a.get("metadata") or {}
        impact = meta.get("expected_uplift_pt", meta.get("estimated_margin_recovery_usd", ""))
        items.append({
            "id": f"appr-{a.get('approval_id')}",
            "ts": a.get("created_at") or a.get("updated_at"),
            "source": "governance.approval",
            "kind": "approval",
            "signal": a.get("title", ""),
            "insight": f"{str(a.get('type', 'action')).replace('_', ' ').title()} requested by {a.get('requester', 'agent')}",
            "foresight": f"Expected impact: {impact}" if impact else "",
            "action": "Human decision required before execution" if status_ == "pending" else f"{status_.title()} by human approver",
            "governance": {"status": status_, "approver": a.get("approver"), "reversible": meta.get("reversible", True)},
            "outcome": "Executed under approved plan" if status_ == "approved" else None,
            "verification": {"status": "pending" if status_ == "approved" else "n/a"},
            "refs": {
                "approval_id": a.get("approval_id"),
                **{k: v for k, v in meta.items() if k.endswith("_ref") or k.endswith("_id")},
            },
        })

    # 4) Audit chain — governance trail
    try:
        from eaip.audit_chain.chain import AuditChain

        chain = request.app.state.lifecycle.platform.container.try_resolve(AuditChain)
        if chain is not None:
            for rec in chain.list_for_tenant(tenant_id):
                d = rec.model_dump(mode="json") if hasattr(rec, "model_dump") else dict(rec)
                meta = d.get("metadata") or {}
                rid = d.get("record_id", d.get("id"))
                items.append({
                    "id": f"audit-{rid}",
                    "ts": d.get("timestamp"),
                    "source": "audit.chain",
                    "kind": "audit",
                    "signal": str(d.get("action", "")).replace(".", " ").title(),
                    "insight": str(d.get("action", "")),
                    "foresight": "",
                    "action": f"Recorded actor: {d.get('actor', 'system')}",
                    "governance": {"status": "audited", "actor": d.get("actor"), "hash_present": bool(d.get("hash"))},
                    "outcome": None,
                    "verification": {"status": "chain-verified"},
                    "refs": {k: v for k, v in meta.items() if isinstance(v, str)},
                })
    except Exception:
        pass

    # 5) Decision logs from persistence (best-effort)
    try:
        from eaip.infrastructure.db.connection import DatabaseConnection

        rows = await DatabaseConnection.fetch(
            "SELECT id, decision_type, context, outcome, timestamp FROM decision_logs "
            "WHERE tenant_id = $1 ORDER BY timestamp DESC LIMIT $2",
            tenant_id, 50,
        )
        for row in rows or []:
            ctx = row["context"] if isinstance(row["context"], dict) else json.loads(row["context"] or "{}")
            out = row["outcome"] if isinstance(row["outcome"], dict) else json.loads(row["outcome"] or "{}")
            alts = ctx.get("alternatives_considered") or []
            selected = next((a.get("option") for a in alts if a.get("selected")), None)
            rejected = [f"{a.get('option')} ({a.get('rejected_because', '')})" for a in alts if not a.get("selected")]
            items.append({
                "id": f"dec-{row['id']}",
                "ts": str(row["timestamp"]),
                "source": "decision.log",
                "kind": "decision",
                "signal": ctx.get("summary", ""),
                "insight": ctx.get("signal", ""),
                "foresight": ctx.get("predicted_impact", ""),
                "action": f"Selected: {selected or ctx.get('summary', 'plan')}",
                "governance": {"status": out.get("status", "logged")},
                "outcome": out.get("result"),
                "verification": {"status": "linked" if ctx.get("prediction_ref") else "none"},
                "refs": {
                    "decision_id": row["id"],
                    "prediction_ref": ctx.get("prediction_ref"),
                    "simulation_ref": ctx.get("simulation_ref"),
                    "alternatives_rejected": rejected,
                },
            })
    except Exception:
        pass

    seen: set[str] = set()
    deduped = []
    for it in items:
        if it["id"] in seen or it["ts"] is None:
            continue
        seen.add(it["id"])
        deduped.append(it)
    deduped.sort(key=lambda x: _parse_ts(x.get("ts")), reverse=True)

    return {
        "tenant_id": tenant_id,
        "count": len(deduped[:limit]),
        "items": deduped[:limit],
    }


# ---------------------------------------------------------------------------
# Explain This
# ---------------------------------------------------------------------------


@router.get("/explain")
async def explain(
    request: Request,
    entity_type: str = Query(default=""),
    entity_id: str = Query(default=""),
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    from eaip.kgraph.graph import KnowledgeGraph
    from eaip.kgraph.index import GraphIndex
    from eaip.http.routers import m2_intelligence as _m2

    await _m2.ensure_loaded()
    container = request.app.state.lifecycle.platform.container
    graph = container.try_resolve(KnowledgeGraph)
    idx = container.try_resolve(GraphIndex)

    ent = None
    related: list[dict[str, Any]] = []
    if graph is not None and entity_id:
        try:
            e = await graph.get_entity(entity_id)
        except Exception:
            e = None
        if e is not None:
            ent = {
                "id": e.id,
                "type": e.type,
                "name": e.name,
                "description": e.description,
                "tags": list(getattr(e, "tags", []) or []),
            }
        if idx is not None:
            try:
                neighbor_ids = await idx.neighbors(entity_id, max_hops=1, limit=8)
            except Exception:
                neighbor_ids = []
            for nid in neighbor_ids or []:
                try:
                    ne = await graph.get_entity(nid)
                except Exception:
                    ne = None
                if ne is not None:
                    related.append({"id": ne.id, "type": ne.type, "name": ne.name})

    preds = [
        p for p in _m2._predictions
        if p.get("tenant_id") == tenant_id and (not entity_id or p.get("target_entity") == entity_id)
    ]
    preds.sort(key=lambda p: _parse_ts(p.get("created_at")), reverse=True)
    latest_pred = preds[0] if preds else None

    what = (ent.get("description") if isinstance(ent, dict) else "") or ""
    why = ""
    recommend = ""
    if latest_pred is not None:
        acc = _accuracy_pct(latest_pred)
        why = latest_pred.get("business_impact") or ""
        if latest_pred.get("actual_outcome") is not None:
            recommend = (
                f"Prediction verified at {acc}% accuracy "
                f"(predicted {latest_pred.get('predicted_value')}, actual {latest_pred.get('actual_outcome')})."
            )
        else:
            recommend = (
                f"Open prediction: {latest_pred.get('metric', '')} forecast at "
                f"{latest_pred.get('predicted_value')} ({latest_pred.get('horizon')}). Monitor or simulate interventions."
            )
    if not why:
        why = "Part of the enterprise knowledge graph; relationships show how it connects."

    return {
        "tenant_id": tenant_id,
        "entity": ent,
        "what": what,
        "why_it_matters": why,
        "data_sources": ["knowledge-graph"] + (["m2.predictions"] if preds else []),
        "freshness": latest_pred.get("created_at") if latest_pred else None,
        "related": related,
        "open_predictions": len([p for p in preds if p.get("actual_outcome") is None]),
        "recommendation": recommend,
        "ask_conductor_context": {
            "entity_id": entity_id,
            "entity_name": (ent or {}).get("name", entity_id) if isinstance(ent, dict) else entity_id,
            "route": f"/{entity_type}s/{entity_id}" if entity_type else "",
        },
    }


# ---------------------------------------------------------------------------
# Attention Center — where does a human need to intervene?
# ---------------------------------------------------------------------------


@router.get("/attention")
async def attention_center(
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    from eaip.http.routers import approval_center as _ac
    from eaip.http.routers import m2_intelligence as _m2

    await _m2.ensure_loaded()
    items: list[dict[str, Any]] = []

    # Needs approval
    for a in getattr(_ac, "_approvals", []):
        if a.get("tenant_id") != tenant_id:
            continue
        if a.get("status") == "pending":
            meta = a.get("metadata") or {}
            items.append({
                "id": f"appr-{a.get('approval_id')}",
                "category": "needs_approval",
                "priority": 0.95 if meta.get("risk_level") in ("high", "medium") else 0.8,
                "title": a.get("title", ""),
                "why": f"{str(a.get('type', 'action')).replace('_', ' ').title()} requested by {a.get('requester', 'agent')}",
                "impact": meta.get("expected_uplift_pt", meta.get("estimated_margin_recovery_usd", "")),
                "actions": [
                    {"kind": "approve", "approval_id": a.get("approval_id")},
                    {"kind": "reject", "approval_id": a.get("approval_id")},
                    {"kind": "defer", "approval_id": a.get("approval_id")},
                ],
                "refs": {k: v for k, v in meta.items() if k.endswith("_ref") or k.endswith("_id")},
            })

    # At risk (radar score >= 0.7)
    for r in _m2._radar:
        if r.get("tenant_id") != tenant_id:
            continue
        score = float(r.get("score", 0))
        if r.get("type") == "risk" and score >= 0.7:
            items.append({
                "id": f"risk-{r['radar_id']}",
                "category": "at_risk",
                "priority": score,
                "title": r.get("title", ""),
                "why": "Driven by: " + ", ".join(r.get("factors") or []),
                "impact": f"Risk score {score:.2f}",
                "actions": [{"kind": "explain", "ref": r["radar_id"]}, {"kind": "simulate"}],
                "refs": {"radar_id": r["radar_id"]},
            })

    # Verify — evaluated predictions with accuracy below verified threshold, or pending actuals on resolved horizon
    for p in _m2._predictions:
        if p.get("tenant_id") != tenant_id:
            continue
        acc = p.get("accuracy")
        if p.get("verification_status") not in ("verified",) and p.get("actual_outcome") is None:
            items.append({
                "id": f"verify-{p['prediction_id']}",
                "category": "waiting",
                "priority": float(p.get("confidence", 0.5)),
                "title": f"Awaiting actual outcome: {p.get('metric')} for {p.get('target_entity')}",
                "why": f"Predicted {p.get('predicted_value')} ({p.get('horizon')}); verification pending",
                "impact": p.get("business_impact", ""),
                "actions": [{"kind": "explain", "ref": p["prediction_id"]}],
                "refs": {"prediction_id": p["prediction_id"], "target_entity": p.get("target_entity")},
            })

    # Recommended — radar opportunities
    for r in _m2._radar:
        if r.get("tenant_id") != tenant_id:
            continue
        if r.get("type") == "opportunity":
            items.append({
                "id": f"opp-{r['radar_id']}",
                "category": "recommended",
                "priority": float(r.get("score", 0.5)),
                "title": r.get("title", ""),
                "why": "; ".join(r.get("factors") or []),
                "impact": f"Opportunity score {float(r.get('score', 0)):.2f}",
                "actions": [{"kind": "explain", "ref": r["radar_id"]}, {"kind": "simulate"}],
                "refs": {"radar_id": r["radar_id"]},
            })

    items.sort(key=lambda x: (-x.get("priority", 0), x.get("title", "")))
    counts: dict[str, int] = {}
    for it in items:
        counts[it["category"]] = counts.get(it["category"], 0) + 1
    return {"tenant_id": tenant_id, "count": len(items), "counts": counts, "items": items}


# ---------------------------------------------------------------------------
# Next Best Action — grounded recommendations from live signals
# ---------------------------------------------------------------------------


@router.get("/next-best-actions")
async def next_best_actions(
    tenant_id: str = Depends(get_tenant_id),
    limit: int = Query(default=3, le=10),
) -> dict[str, Any]:
    from eaip.http.routers import approval_center as _ac
    from eaip.http.routers import m2_intelligence as _m2

    await _m2.ensure_loaded()
    actions: list[dict[str, Any]] = []

    preds_by_entity: dict[str, list[dict[str, Any]]] = {}
    for p in _m2._predictions:
        if p.get("tenant_id") == tenant_id:
            preds_by_entity.setdefault(str(p.get("target_entity")), []).append(p)

    def _acc(p: dict[str, Any]) -> float | None:
        a = p.get("accuracy")
        try:
            return float(a) if a is not None else None
        except Exception:
            return None

    # 1) Open risks with a proven track record → recommend simulate/approve path
    for r in _m2._radar:
        if r.get("tenant_id") != tenant_id or r.get("type") != "risk":
            continue
        score = float(r.get("score", 0))
        if score < 0.7:
            continue
        related = preds_by_entity.get(str(r.get("title", "")), [])
        evidence = list(r.get("factors") or [])
        confidence = 0.75
        track = ""
        for p in _m2._predictions:
            if p.get("tenant_id") == tenant_id and p.get("actual_outcome") is not None:
                a = _acc(p)
                if a is not None:
                    confidence = max(confidence, min(0.95, a))
                    track = (
                        f"EAIP's last prediction on this estate was {round(a * 100, 1)}% accurate "
                        f"(predicted {p.get('predicted_value')}, actual {p.get('actual_outcome')})."
                    )
                    break
        pending_appr = next(
            (a for a in getattr(_ac, "_approvals", [])
             if a.get("tenant_id") == tenant_id and a.get("status") == "pending"),
            None,
        )
        actions.append({
            "id": f"nba-risk-{r['radar_id']}",
            "title": f"Mitigate: {r.get('title', '')}",
            "rationale": "Signals: " + ", ".join(evidence),
            "recommendation": "Run a safe simulation of the recommended intervention, then approve the remediation plan.",
            "expected_impact": r.get("business_impact") or "Reduces projected downside per risk model.",
            "confidence": round(confidence, 2),
            "risk_level": "high" if score >= 0.85 else "medium",
            "track_record": track,
            "requires_approval": pending_appr is not None,
            "approval_id": pending_appr.get("approval_id") if pending_appr else None,
            "simulate_hint": True,
            "source_refs": {"radar_id": r["radar_id"]},
            "grounding": ["m2.radar"] + (["m2.predictions"] if track else []),
        })

    # 2) Opportunities → recommend exploit
    for r in _m2._radar:
        if r.get("tenant_id") != tenant_id or r.get("type") != "opportunity":
            continue
        score = float(r.get("score", 0))
        if score < 0.5:
            continue
        actions.append({
            "id": f"nba-opp-{r['radar_id']}",
            "title": f"Exploit: {r.get('title', '')}",
            "rationale": "; ".join(r.get("factors") or []),
            "recommendation": "Simulate the upside scenario and, if confirmed, create an approved mission to capture it.",
            "expected_impact": f"Opportunity score {score:.2f} based on current signals.",
            "confidence": round(min(0.9, 0.5 + score / 2), 2),
            "risk_level": "low",
            "track_record": "",
            "requires_approval": False,
            "approval_id": None,
            "simulate_hint": True,
            "source_refs": {"radar_id": r["radar_id"]},
            "grounding": ["m2.radar"],
        })

    actions.sort(key=lambda a: ({"high": 3, "medium": 2, "low": 1}.get(a.get("risk_level", "low"), 1), -a.get("confidence", 0)), reverse=True)
    return {"tenant_id": tenant_id, "count": len(actions[:limit]), "items": actions[:limit]}



@router.get("/lineage/decision/{decision_id}")
async def decision_lineage(
    request: Request,
    decision_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> dict[str, Any]:
    from eaip.http.routers import approval_center as _ac
    from eaip.http.routers import m2_intelligence as _m2
    from eaip.infrastructure.db.connection import DatabaseConnection

    await _m2.ensure_loaded()
    dec = None
    try:
        row = await DatabaseConnection.fetchrow(
            "SELECT id, tenant_id, decision_type, context, outcome, timestamp FROM decision_logs "
            "WHERE id = $1 AND tenant_id = $2",
            decision_id, tenant_id,
        )
        if row:
            ctx0 = row["context"] if isinstance(row["context"], dict) else json.loads(row["context"] or "{}")
            out0 = row["outcome"] if isinstance(row["outcome"], dict) else json.loads(row["outcome"] or "{}")
            dec = {
                "id": row["id"], "decision_type": row["decision_type"],
                "context": ctx0, "outcome": out0, "timestamp": str(row["timestamp"]),
            }
    except Exception:
        pass
    if dec is None:
        raise HTTPException(status_code=404, detail="decision not found")

    ctx = dec["context"]
    pred_ref = ctx.get("prediction_ref")

    # Prediction + verification
    prediction = next((p for p in _m2._predictions if p.get("prediction_id") == pred_ref), None)
    verification = None
    if prediction is not None:
        acc = _accuracy_pct(prediction)
        verification = {
            "prediction_id": prediction["prediction_id"],
            "metric": prediction.get("metric"),
            "baseline": prediction.get("baseline"),
            "predicted": prediction.get("predicted_value"),
            "actual": prediction.get("actual_outcome"),
            "actual_at": prediction.get("actual_at"),
            "error": prediction.get("prediction_error"),
            "accuracy_pct": acc,
            "confidence": prediction.get("confidence"),
            "status": ("verified" if (acc is not None and acc >= 85) else str(prediction.get("verification_status", "evaluated"))),
            "assumptions": prediction.get("assumptions"),
            "synthetic": prediction.get("synthetic", True),
        }

    # Approvals referencing this decision / its prediction / its mission
    approvals = []
    for a in getattr(_ac, "_approvals", []):
        if a.get("tenant_id") != tenant_id:
            continue
        meta = a.get("metadata") or {}
        if pred_ref and meta.get("prediction_ref") == pred_ref:
            approvals.append({
                "approval_id": a.get("approval_id"),
                "title": a.get("title"),
                "status": a.get("status"),
                "risk_level": meta.get("risk_level"),
                "reversible": meta.get("reversible", True),
            })

    # Audit trail touching this decision / its refs
    audit = []
    try:
        from eaip.audit_chain.chain import AuditChain

        chain = request.app.state.lifecycle.platform.container.try_resolve(AuditChain)
        if chain is not None:
            for rec in chain.list_for_tenant(tenant_id):
                d = rec.model_dump(mode="json") if hasattr(rec, "model_dump") else dict(rec)
                meta = d.get("metadata") or {}
                linked = (
                    meta.get("decision_ref") == decision_id
                    or (pred_ref and meta.get("prediction_ref") == pred_ref)
                    or (pred_ref and any(meta.get(k) == v for k, v in ({"prediction_ref": pred_ref},).items()))
                )
                if linked:
                    audit.append({**d, "hash_present": bool(d.get("hash"))})
    except Exception:
        pass

    # Mission linkage via approval metadata
    mission_ref = None
    workflow_ref = None
    try:
        from eaip.http.routers import approval_center as _ac2

        for a in getattr(_ac2, "_approvals", []):
            if a.get("tenant_id") != tenant_id:
                continue
            meta = a.get("metadata") or {}
            if pred_ref and meta.get("prediction_ref") == pred_ref:
                mission_ref = meta.get("mission_id")
                workflow_ref = meta.get("workflow_id")
                break
    except Exception:
        pass

    return {
        "tenant_id": tenant_id,
        "decision_id": decision_id,
        "signal": {
            "summary": ctx.get("summary", ""),
            "source_signal": ctx.get("signal", ""),
        },
        "evidence": prediction.get("evidence") if prediction else [],
        "assumptions": prediction.get("assumptions") if prediction else [],
        "alternatives": ctx.get("alternatives_considered", []),
        "simulation": {"ref": ctx.get("simulation_ref")} if ctx.get("simulation_ref") else None,
        "prediction": (
            {"ref": pred_ref, "predicted_value": prediction.get("predicted_value"),
             "confidence": prediction.get("confidence"), "horizon": prediction.get("horizon")}
            if prediction else ({"ref": pred_ref} if pred_ref else None)
        ),
        "risk": {"business_impact": ctx.get("predicted_impact", "")},
        "approval": approvals[0] if approvals else None,
        "selected_option": next(
            (a.get("option") for a in (ctx.get("alternatives_considered") or []) if a.get("selected")),
            ctx.get("summary", ""),
        ),
        "execution": {
            "mission_id": mission_ref,
            "workflow_id": workflow_ref,
            "outcome_status": dec["outcome"].get("status", "logged"),
        },
        "actual_outcome": verification,
        "accuracy": verification.get("accuracy_pct") if verification else None,
        "audit_proof": audit,
        "verification_status": verification.get("status") if verification else "unverified",
    }
