from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.workflow.composer import WorkflowComposer

router = APIRouter(prefix="/workflow-compose", tags=["workflow-compose"])


def _composer(req: Request) -> WorkflowComposer:
    c = req.app.state.lifecycle.platform.container.try_resolve(WorkflowComposer)
    if c is None:
        c = WorkflowComposer()
        req.app.state.lifecycle.platform.container.register_instance(WorkflowComposer, c)
    return c


@router.post("/compose")
async def compose(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    goal = str(body.get("goal", "")).strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal required")
    composer = _composer(request)
    result = composer.compose(goal, constraints=body.get("constraints") or body.get("budget"))
    # Publish workflow as DRAFT via registry if available
    try:
        from eaip.workflow.registry import WorkflowRegistry
        from eaip.workflow.models import WorkflowDefinition, WorkflowEdge, WorkflowStep
        reg = request.app.state.lifecycle.platform.container.try_resolve(WorkflowRegistry)
        wf_data = result["workflow"]
        if reg is not None and result["status"] == "draft":
            wf = WorkflowDefinition.model_validate(wf_data)
            await reg.create(wf, metadata={"tenant_id": tenant_id, "composed": True, "risk": result["risk"]})
    except Exception:
        pass
    return result


@router.post("/validate")
async def validate(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    composer = _composer(request)
    wf_data = body.get("workflow") or body
    try:
        from eaip.workflow.models import WorkflowDefinition
        wf = WorkflowDefinition.model_validate(wf_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid workflow: {exc}") from exc
    has_cycle = composer._has_cycle(wf)
    return {"valid": not has_cycle, "has_cycle": has_cycle, "step_count": len(wf.steps)}
