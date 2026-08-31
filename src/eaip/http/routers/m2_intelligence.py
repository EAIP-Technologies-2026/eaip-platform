from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.logging.context import get_logger

log = get_logger("eaip.http.routers.m2_intelligence")

router = APIRouter(prefix="/m2", tags=["m2"])

_predictions: list[dict[str, Any]] = []
_events_intel: list[dict[str, Any]] = []
_briefings: list[dict[str, Any]] = []
_radar: list[dict[str, Any]] = []

_hydrated = False
_hydrate_lock: asyncio.Lock | None = None


async def _persist(table: str, id_col: str, rec_id: str, tenant_id: str, payload: dict[str, Any]) -> None:
    """Write-through to the durable M2 store; memory remains the read cache."""
    try:
        from eaip.infrastructure.db.connection import DatabaseConnection

        if DatabaseConnection.get_pool() is None:
            return
        await DatabaseConnection.execute(
            f"INSERT INTO {table} ({id_col}, tenant_id, payload) VALUES ($1, $2, $3::jsonb) "
            f"ON CONFLICT ({id_col}, tenant_id) DO UPDATE SET payload = EXCLUDED.payload",
            rec_id, tenant_id, json.dumps(payload, default=str),
        )
    except Exception as exc:
        log.warning("m2.persist_failed", table=table, error=repr(exc))


async def hydrate_from_db() -> int:
    """Load durable M2 state into the in-process cache. Safe to call repeatedly."""
    global _hydrated

    def _payload(raw: Any) -> dict[str, Any]:
        if isinstance(raw, str):
            return dict(json.loads(raw))
        return dict(raw)

    try:
        from eaip.infrastructure.db.connection import DatabaseConnection

        if DatabaseConnection.get_pool() is None:
            return 0
        merged = 0
        rows = await DatabaseConnection.fetch("SELECT prediction_id, tenant_id, payload FROM m2_predictions")
        known = {(p["prediction_id"], p["tenant_id"]) for p in _predictions}
        for row in rows or []:
            if (row["prediction_id"], row["tenant_id"]) not in known:
                _predictions.append(_payload(row["payload"]))
                merged += 1
        rows = await DatabaseConnection.fetch("SELECT radar_id, tenant_id, payload FROM m2_radar")
        known = {(r["radar_id"], r["tenant_id"]) for r in _radar}
        for row in rows or []:
            if (row["radar_id"], row["tenant_id"]) not in known:
                _radar.append(_payload(row["payload"]))
                merged += 1
        rows = await DatabaseConnection.fetch("SELECT briefing_id, tenant_id, payload FROM m2_briefings")
        known = {(b["briefing_id"], b["tenant_id"]) for b in _briefings}
        for row in rows or []:
            if (row["briefing_id"], row["tenant_id"]) not in known:
                _briefings.append(_payload(row["payload"]))
                merged += 1
        _hydrated = True
        if merged:
            log.info("m2.hydrated", merged=merged)
        return merged
    except Exception as exc:
        log.warning("m2.hydrate_failed", error=repr(exc))
        return 0


async def ensure_loaded() -> None:
    """Hydrate once per process before any read of M2 state."""
    global _hydrate_lock
    if _hydrated:
        return
    if _hydrate_lock is None:
        _hydrate_lock = asyncio.Lock()
    async with _hydrate_lock:
        if not _hydrated:
            await hydrate_from_db()

@router.post("/predictions", status_code=201)
async def create_prediction(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # Spec fields: prediction_id, tenant, target entity, metric, baseline, predicted value, horizon, confidence, assumptions, evidence, created_at, actual value, actual_at, error, accuracy, verification status, synthetic
    # Preserve backward compat with existing callers (tests use target/predicted_value/confidence only)
    rec: dict[str, Any] = {
        "prediction_id": body.get("prediction_id") or f"pred-{uuid.uuid4().hex[:6]}",
        "tenant_id": tenant_id,
        "target": str(body.get("target", body.get("target_entity", "unknown"))),
        "target_entity": str(body.get("target_entity", body.get("target", "unknown"))),
        "metric": str(body.get("metric", body.get("target", "unknown"))),
        "horizon": str(body.get("horizon", "7d")),
        "input_refs": body.get("input_refs") or [],
        "model": str(body.get("model", "synthetic")),
        "predicted_value": body.get("predicted_value"),
        "baseline": body.get("baseline"),
        "confidence": float(body.get("confidence", 0.5)),
        "assumptions": body.get("assumptions") or [],
        "evidence": body.get("evidence") or [],
        "business_impact": body.get("business_impact"),
        "confidence_interval": body.get("confidence_interval"),
        "verification_status": str(body.get("verification_status", "predicted")),
        "synthetic": bool(body.get("synthetic", True)),
        "created_at": body.get("created_at") or datetime.now(UTC).isoformat(),
        "status": "predicted",
        "actual_outcome": None,
        "actual_value": None,
        "actual_at": None,
        "prediction_error": None,
        "accuracy": None,
        "error": None,
    }
    # Also honor explicit accuracy/verification if caller sends them at creation (rare)
    if body.get("accuracy") is not None:
        rec["accuracy"] = body.get("accuracy")
    # dedupe by prediction_id+tenant — replace if exists for seeding idempotency
    for idx, existing in enumerate(_predictions):
        if existing.get("prediction_id") == rec["prediction_id"] and existing.get("tenant_id") == tenant_id:
            _predictions[idx] = {**existing, **rec}
            await _persist("m2_predictions", "prediction_id", rec["prediction_id"], tenant_id, _predictions[idx])
            return _predictions[idx]
    _predictions.append(rec)
    await _persist("m2_predictions", "prediction_id", rec["prediction_id"], tenant_id, rec)
    return rec

@router.get("/predictions")
async def list_predictions(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    await ensure_loaded()
    return [p for p in _predictions if p["tenant_id"] == tenant_id]

@router.post("/predictions/{prediction_id}/actual")
async def record_actual(request: Request, prediction_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    await ensure_loaded()
    for p in _predictions:
        if p["prediction_id"] == prediction_id and p["tenant_id"] == tenant_id:
            actual = body.get("actual_outcome", body.get("actual_value"))
            p["actual_outcome"] = actual
            p["actual_value"] = actual
            p["actual_at"] = body.get("actual_at") or datetime.now(UTC).isoformat()
            try:
                if p["predicted_value"] is not None and actual is not None:
                    err = abs(float(p["predicted_value"]) - float(actual))
                    p["prediction_error"] = err
                    p["error"] = err
                    # accuracy = 1 - relative error, clamped 0..1
                    denom = abs(float(p["predicted_value"])) if float(p["predicted_value"]) != 0 else 1.0
                    acc = max(0.0, min(1.0, 1.0 - err / denom))
                    p["accuracy"] = round(acc, 4)
                    p["verification_status"] = "verified" if acc >= 0.85 else "evaluated"
                else:
                    p["prediction_error"] = None
                    p["accuracy"] = body.get("accuracy")
                    p["verification_status"] = str(body.get("verification_status", "evaluated"))
            except Exception:
                p["prediction_error"] = None
                p["error"] = None
            p["status"] = "evaluated"
            # also accept explicit overrides
            if body.get("verification_status"):
                p["verification_status"] = str(body["verification_status"])
            if body.get("accuracy") is not None:
                p["accuracy"] = float(body["accuracy"])
            await _persist("m2_predictions", "prediction_id", prediction_id, tenant_id, p)
            return p
    raise HTTPException(status_code=404, detail="prediction not found")

@router.get("/predictions/evaluation")
async def prediction_evaluation(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    await ensure_loaded()
    tenant_preds = [p for p in _predictions if p["tenant_id"] == tenant_id and p["status"] == "evaluated" and p["prediction_error"] is not None]
    if not tenant_preds:
        return {"tenant_id": tenant_id, "count": 0, "avg_error": None, "avg_accuracy": None, "verified": 0}
    avg = sum(float(p["prediction_error"]) for p in tenant_preds) / len(tenant_preds)
    acc_vals = [float(p["accuracy"]) for p in tenant_preds if p.get("accuracy") is not None]
    avg_acc = round(sum(acc_vals) / len(acc_vals), 4) if acc_vals else None
    verified = sum(1 for p in tenant_preds if p.get("verification_status") == "verified")
    return {"tenant_id": tenant_id, "count": len(tenant_preds), "avg_error": round(avg, 4), "avg_accuracy": avg_acc, "verified": verified, "predictions": tenant_preds[:10]}

@router.post("/events/ingest", status_code=201)
async def ingest_event(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"event_id": body.get("event_id") or f"evt-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "type": str(body.get("type", "generic")), "payload": body.get("payload") or {}, "created_at": datetime.now(UTC).isoformat()}
    _events_intel.append(rec)
    if len(_events_intel) > 2000:
        del _events_intel[:500]
    return rec

@router.get("/events")
async def list_events(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), limit: int = 50) -> list[dict[str, Any]]:
    await ensure_loaded()
    return [e for e in _events_intel if e["tenant_id"] == tenant_id][-limit:]

@router.post("/events/correlate")
async def correlate_events(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    # simple correlation by type
    tenant_events = [e for e in _events_intel if e["tenant_id"] == tenant_id]
    by_type: dict[str, list[dict[str, Any]]] = {}
    for e in tenant_events:
        by_type.setdefault(e["type"], []).append(e)
    clusters = [{"type": k, "count": len(v), "event_ids": [e["event_id"] for e in v[:5]]} for k, v in by_type.items()]
    return {"tenant_id": tenant_id, "clusters": clusters, "total": len(tenant_events)}

@router.post("/events/causal")
async def causal_chain(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    event_id = str(body.get("event_id", ""))
    # infer chain: find events with same tenant ordered by time
    tenant_events = sorted([e for e in _events_intel if e["tenant_id"] == tenant_id], key=lambda x: x["created_at"])
    chain = [{"event_id": e["event_id"], "type": e["type"], "observed": True} for e in tenant_events[-5:]]
    if event_id:
        chain.append({"event_id": event_id, "inferred": True, "note": "requested root"})
    return {"tenant_id": tenant_id, "chain": chain, "distinction": "observed vs inferred — correlation not causation"}

@router.post("/events/replay")
async def replay_events(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ids = body.get("event_ids") or []
    mode = str(body.get("mode", "simulation"))
    # never duplicate irreversible production actions — simulation mode
    matched = [e for e in _events_intel if e["tenant_id"] == tenant_id and (not ids or e["event_id"] in ids)]
    return {"tenant_id": tenant_id, "replayed": len(matched), "mode": mode, "idempotent": True, "note": "replay in simulation mode — no irreversible duplicate"}

@router.post("/briefings", status_code=201)
async def create_briefing(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    period = str(body.get("period", "daily"))
    rec = {"briefing_id": f"brief-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "period": period, "what_changed": body.get("what_changed") or f"Synthetic briefing for {tenant_id}", "why": "synthetic fixture", "risks": body.get("risks") or [], "opportunities": body.get("opportunities") or [], "decisions_needed": body.get("decisions_needed") or [], "actions_underway": body.get("actions_underway") or [], "expected_outcomes": body.get("expected_outcomes") or [], "confidence": float(body.get("confidence", 0.5)), "created_at": datetime.now(UTC).isoformat()}
    _briefings.append(rec)
    await _persist("m2_briefings", "briefing_id", rec["briefing_id"], tenant_id, rec)
    return rec

@router.get("/briefings")
async def list_briefings(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    await ensure_loaded()
    return [b for b in _briefings if b["tenant_id"] == tenant_id]

@router.post("/radar", status_code=201)
async def create_radar_entry(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = {"radar_id": f"radar-{uuid.uuid4().hex[:6]}", "tenant_id": tenant_id, "type": str(body.get("type", "risk")), "category": str(body.get("category", "operational")), "title": str(body.get("title", "risk")), "score": float(body.get("score", 0.5)), "factors": body.get("factors") or ["synthetic"], "created_at": datetime.now(UTC).isoformat()}
    _radar.append(rec)
    await _persist("m2_radar", "radar_id", rec["radar_id"], tenant_id, rec)
    return rec

@router.get("/radar")
async def list_radar(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), type: str = "") -> list[dict[str, Any]]:
    await ensure_loaded()
    items = [r for r in _radar if r["tenant_id"] == tenant_id]
    if type:
        items = [r for r in items if r["type"] == type]
    return sorted(items, key=lambda x: x["score"], reverse=True)[:50]

@router.post("/events/strategy")
async def event_strategy(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    event_id = str(body.get("event_id", ""))
    return {"tenant_id": tenant_id, "event_id": event_id, "strategy": "assess impact → check policy/risk → simulate if needed → approval/action", "classified_as": str(body.get("classification", "info")), "next": "simulate"}
