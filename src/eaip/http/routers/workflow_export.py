from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user
from eaip.logging.context import get_logger
from eaip.workflow.registry import WorkflowRegistry

router = APIRouter(prefix="/workflows/{workflow_id}/export", tags=["workflows"], dependencies=[Depends(get_current_user)])
log = get_logger("eaip.http.routers.workflow_export")


def _get_registry(request: Request) -> WorkflowRegistry:
    return request.app.state.lifecycle.platform.container.resolve(WorkflowRegistry)


@router.get("/json")
async def export_workflow_json(request: Request, workflow_id: str):
    registry = _get_registry(request)
    wf = await registry.get(workflow_id)
    if wf is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Workflow not found")

    status = await registry.get_status(workflow_id)
    metadata = await registry.get_metadata(workflow_id)

    export_data = {
        "format": "eaip-workflow-v1",
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "workflow": {
            "id": wf.id,
            "name": wf.name,
            "description": getattr(wf, "description", ""),
            "version": wf.version,
            "status": status.value if status else "unknown",
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "agent_id": s.agent_id,
                    "tool_name": s.tool_name,
                    "prompt": s.prompt,
                    "input": s.input,
                    "timeout_seconds": s.timeout_seconds,
                }
                for s in wf.steps
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "label": e.label,
                    "condition": e.condition.value,
                }
                for e in wf.edges
            ],
            "metadata": metadata,
        },
    }
    return export_data


@router.post("/import")
async def import_workflow(request: Request, workflow_id: str, body: dict):
    registry = _get_registry(request)
    wf = await registry.get(workflow_id)
    if wf is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Workflow not found")

    import_data = body.get("workflow", body)
    from eaip.workflow.models import WorkflowDefinition, WorkflowEdge, WorkflowStep

    steps_data = import_data.get("steps", [])
    edges_data = import_data.get("edges", [])

    steps = tuple(
        WorkflowStep(
            id=s.get("id", f"imp-{i}"),
            name=s.get("name", f"Imported {i}"),
            agent_id=s.get("agent_id", ""),
            tool_name=s.get("tool_name", ""),
            prompt=s.get("prompt", ""),
            input=s.get("input", {}),
            timeout_seconds=s.get("timeout_seconds", 0.0),
        )
        for i, s in enumerate(steps_data)
    )
    edges = tuple(
        WorkflowEdge(
            source_id=e.get("source_id", ""),
            target_id=e.get("target_id", ""),
            label=e.get("label", ""),
        )
        for e in edges_data
    )

    await registry.update(workflow_id, steps=steps, edges=edges)
    return {"status": "imported", "workflowId": workflow_id, "stepCount": len(steps)}
