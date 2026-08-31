from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/wave2", tags=["wave2-pipeline"])


def _pipeline(request: Request):  # type: ignore[no-untyped-def]
    from eaip.orchestration.wave2_pipeline import Wave2Pipeline
    from eaip.ops_intelligence.service import OpsIntelligenceService
    from eaip.intelligence.cognition import CognitiveEngine
    from eaip.methodology.registry import MethodologyRegistry
    from eaip.intelligence.decision_service import DecisionIntelligenceService
    from eaip.simulation.scenario_service import ScenarioEngine
    from eaip.intelligence.coordination import CoordinationEngine
    from eaip.workforce.digital_service import DigitalWorkforceService
    from eaip.improvement.service import ImprovementService

    c = request.app.state.lifecycle.platform.container
    pipe = c.try_resolve(Wave2Pipeline)
    if pipe is not None:
        return pipe
    pipe = Wave2Pipeline(
        ops_service=c.try_resolve(OpsIntelligenceService) or OpsIntelligenceService(),
        cognition=c.try_resolve(CognitiveEngine),
        methodology_registry=c.try_resolve(MethodologyRegistry),
        decision_service=c.try_resolve(DecisionIntelligenceService),
        scenario_engine=c.try_resolve(ScenarioEngine),
        coordination=c.try_resolve(CoordinationEngine),
        workforce=c.try_resolve(DigitalWorkforceService),
        improvement=c.try_resolve(ImprovementService),
        event_bus=None,
    )
    try:
        c.register_instance(Wave2Pipeline, pipe)
    except Exception:
        pass
    return pipe


@router.post("/pipeline/run")
async def run_pipeline(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    pipe = _pipeline(request)
    trigger = body.get("trigger") or body
    if not isinstance(trigger, dict):
        trigger = {"trigger": str(trigger)}
    result = await pipe.run(tenant_id, trigger)
    return result


@router.get("/pipeline/health")
async def pipeline_health(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {"tenant_id": tenant_id, "status": "healthy", "pipeline": "wave2", "steps": ["ops_intelligence", "cognition", "methodology", "decision", "simulation", "coordination", "workforce", "improvement"]}


__all__ = ["router"]
