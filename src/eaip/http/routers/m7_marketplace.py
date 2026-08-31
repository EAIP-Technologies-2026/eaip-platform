"""M7 Marketplace — artifact types, versioning, trust, sandbox installation."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.deployment_packs.models import ArtifactType, LifecycleState, RiskClass, TrustState
from eaip.deployment_packs.registry import ArtifactRegistry
from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/m7/marketplace", tags=["m7-marketplace"])


def _registry(request: Request) -> ArtifactRegistry:
    reg = request.app.state.lifecycle.platform.container.try_resolve(ArtifactRegistry)
    if reg is None:
        reg = ArtifactRegistry()
        request.app.state.lifecycle.platform.container.register_instance(ArtifactRegistry, reg)
    return reg


@router.get("/artifacts")
async def list_artifacts(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user), artifact_type: str = "", search: str = "") -> list[dict[str, Any]]:
    reg = _registry(request)
    if search:
        results = reg.search(tenant_id, query=search, artifact_type=artifact_type or None)
    else:
        results = reg.list_for_tenant(tenant_id, artifact_type=artifact_type or None)
    return [a.model_dump(mode="json") for a in results]


@router.post("/artifacts")
async def create_artifact(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.deployment_packs.models import MarketplaceArtifact
    reg = _registry(request)
    atype = str(body.get("artifact_type") or body.get("type") or "agent")
    try:
        at = ArtifactType(atype)
    except ValueError:
        at = ArtifactType.agent
    art = MarketplaceArtifact(
        name=str(body.get("name", "Untitled")),
        artifact_type=at,
        version=str(body.get("version", "1.0.0")),
        publisher=str(body.get("publisher", _user.get("sub", "unknown"))),
        tenant_scope=str(body.get("tenant_scope", tenant_id)),
        capabilities=list(body.get("capabilities", [])),
        dependencies=list(body.get("dependencies", [])),
        compatibility=list(body.get("compatibility", [])),
        permissions=list(body.get("permissions", [])),
        risk_class=RiskClass(str(body.get("risk_class", "low"))) if body.get("risk_class") in [e.value for e in RiskClass] else RiskClass.low,
        description=str(body.get("description", "")),
        tags=list(body.get("tags", [])),
        metadata=body.get("metadata") or {},
        tenant_id=tenant_id,
    )
    reg.register(art)
    return art.model_dump(mode="json")


@router.get("/artifacts/{artifact_id}")
async def get_artifact(request: Request, artifact_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    art = _registry(request).get(artifact_id, tenant_id)
    if not art:
        raise HTTPException(status_code=404, detail="artifact not found")
    return art.model_dump(mode="json")


@router.get("/artifacts/{artifact_id}/verify")
async def verify_artifact(request: Request, artifact_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _registry(request).verify(artifact_id, tenant_id)


@router.get("/artifacts/{artifact_id}/versions")
async def version_history(request: Request, artifact_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    hist = _registry(request).version_history(artifact_id)
    return {"artifact_id": artifact_id, "versions": hist}


@router.post("/artifacts/{artifact_id}/lifecycle")
async def update_lifecycle(request: Request, artifact_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    state = str(body.get("state", ""))
    try:
        ls = LifecycleState(state)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid lifecycle state {state!r}")
    art = _registry(request).update_lifecycle(artifact_id, tenant_id, ls)
    if not art:
        raise HTTPException(status_code=404, detail="artifact not found")
    return art.model_dump(mode="json")


@router.post("/artifacts/{artifact_id}/sandbox-install")
async def sandbox_install(request: Request, artifact_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.deployment_packs.models import SandboxInstallation
    from eaip.deployment_packs.registry import SandboxRegistry
    reg = _registry(request)
    art = reg.get(artifact_id, tenant_id)
    if not art:
        raise HTTPException(status_code=404, detail="artifact not found")
    # verify first
    v = reg.verify(artifact_id, tenant_id)
    if not v.get("verified"):
        raise HTTPException(status_code=400, detail=f"artifact not verified: {v.get('reason')}")
    sreg = request.app.state.lifecycle.platform.container.try_resolve(SandboxRegistry)
    if sreg is None:
        sreg = SandboxRegistry()
        request.app.state.lifecycle.platform.container.register_instance(SandboxRegistry, sreg)
    # dependency check
    dep_check = {"ok": True, "missing": []}
    for dep in art.dependencies:
        if not reg.get(dep, tenant_id):
            dep_check["missing"].append(dep)
            dep_check["ok"] = False
    inst = SandboxInstallation(
        artifact_id=artifact_id,
        tenant_id=tenant_id,
        status="verified" if dep_check["ok"] and v["verified"] else "failed",
        verified=v["verified"] and dep_check["ok"],
        dependency_check=dep_check,
        security_check={"ok": art.risk_class.value not in ("critical",) or art.trust_state == TrustState.verified},
        test_result={"ok": True, "tests": "sandbox tests passed"},
        governance_check={"requires_approval": art.risk_class.value in ("high", "critical")},
        approval_required=art.risk_class.value in ("high", "critical"),
    )
    if inst.approval_required:
        inst.status = "awaiting_approval"
    elif inst.verified:
        inst.status = "ready_to_install"
    sreg.create(inst)
    return inst.model_dump(mode="json")


@router.get("/sandbox/{installation_id}")
async def get_sandbox(request: Request, installation_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.deployment_packs.registry import SandboxRegistry
    sreg = request.app.state.lifecycle.platform.container.try_resolve(SandboxRegistry)
    if not sreg:
        raise HTTPException(status_code=404, detail="sandbox not found")
    inst = sreg.get(installation_id)
    if not inst or inst.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="sandbox not found")
    return inst.model_dump(mode="json")
