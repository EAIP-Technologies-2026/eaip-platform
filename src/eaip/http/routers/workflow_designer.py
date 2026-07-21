from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from eaip.logging.context import get_logger
from eaip.workflow.models import WorkflowDefinition, WorkflowEdge, WorkflowStep
from eaip.workflow.registry import WorkflowRegistry

router = APIRouter(prefix="/designer", tags=["workflows"])
log = get_logger("eaip.http.routers.workflow_designer")

# In-memory autosave store (replace with PostgreSQL in production)
_autosave_store: dict[str, dict[str, Any]] = {}


def _get_registry(request: Request) -> WorkflowRegistry:
    return request.app.state.lifecycle.platform.container.resolve(WorkflowRegistry)


@router.put("/{workflow_id}")
async def save_designer_state(request: Request, workflow_id: str, body: dict[str, Any]):
    registry = _get_registry(request)
    wf = await registry.get(workflow_id)
    if wf is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_id} not found")

    steps_data = body.get("nodes", [])
    edges_data = body.get("edges", [])
    new_steps = tuple(
        WorkflowStep(
            id=s.get("id", f"step-{i}"),
            name=s.get("label", s.get("name", f"Step {i}")),
            agent_id=s.get("agent_id", ""),
            tool_name=s.get("tool_name", ""),
            prompt=s.get("prompt", ""),
            input=s.get("input", {}),
            timeout_seconds=s.get("timeout_seconds", 0.0),
        )
        for i, s in enumerate(steps_data)
    )
    new_edges = tuple(
        WorkflowEdge(
            source_id=e.get("source", e.get("source_id", "")),
            target_id=e.get("target", e.get("target_id", "")),
            label=e.get("label", ""),
        )
        for e in edges_data
    )
    try:
        await registry.update(workflow_id, steps=new_steps, edges=new_edges)
    except Exception as e:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(e))

    return {
        "status": "saved",
        "workflowId": workflow_id,
        "nodeCount": len(new_steps),
        "edgeCount": len(new_edges),
        "savedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{workflow_id}")
async def load_designer_state(request: Request, workflow_id: str):
    registry = _get_registry(request)
    wf = await registry.get(workflow_id)
    if wf is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Workflow {workflow_id} not found")

    return {
        "id": wf.id,
        "name": wf.name,
        "nodes": [
            {
                "id": s.id,
                "type": "agent",
                "label": s.name,
                "x": 0,
                "y": 0,
                "config": {
                    "agent_id": s.agent_id,
                    "tool_name": s.tool_name,
                    "prompt": s.prompt,
                },
            }
            for s in wf.steps
        ],
        "edges": [
            {
                "id": f"edge-{i}",
                "source": e.source_id,
                "target": e.target_id,
                "label": e.label,
            }
            for i, e in enumerate(wf.edges)
        ],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
    }


@router.post("/{workflow_id}/autosave")
async def autosave_designer_state(request: Request, workflow_id: str, body: dict[str, Any]):
    _autosave_store[workflow_id] = {
        "nodes": body.get("nodes", []),
        "edges": body.get("edges", []),
        "viewport": body.get("viewport", {}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return {"status": "autosaved", "workflowId": workflow_id}


@router.get("/{workflow_id}/autosave")
async def get_autosave_state(request: Request, workflow_id: str):
    state = _autosave_store.get(workflow_id)
    if state is None:
        return {"hasAutosave": False, "workflowId": workflow_id}
    return {
        "hasAutosave": True,
        "workflowId": workflow_id,
        "nodes": state.get("nodes", []),
        "edges": state.get("edges", []),
        "viewport": state.get("viewport", {}),
        "timestamp": state.get("timestamp", ""),
    }


@router.delete("/{workflow_id}/autosave")
async def clear_autosave_state(request: Request, workflow_id: str):
    _autosave_store.pop(workflow_id, None)
    return {"status": "cleared", "workflowId": workflow_id}
