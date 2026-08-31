"""M7 Deployment packs, configs, validation, onboarding — EAIP Core → Industry → Deployment → Customer."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.deployment_packs.registry import DeploymentConfigRegistry, DeploymentPackRegistry, OnboardingRegistry
from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/m7/deployment", tags=["m7-deployment"])


def _pack_reg(request: Request) -> DeploymentPackRegistry:
    reg = request.app.state.lifecycle.platform.container.try_resolve(DeploymentPackRegistry)
    if reg is None:
        reg = DeploymentPackRegistry()
        request.app.state.lifecycle.platform.container.register_instance(DeploymentPackRegistry, reg)
    return reg


def _cfg_reg(request: Request) -> DeploymentConfigRegistry:
    reg = request.app.state.lifecycle.platform.container.try_resolve(DeploymentConfigRegistry)
    if reg is None:
        reg = DeploymentConfigRegistry()
        request.app.state.lifecycle.platform.container.register_instance(DeploymentConfigRegistry, reg)
    return reg


def _ob_reg(request: Request) -> OnboardingRegistry:
    reg = request.app.state.lifecycle.platform.container.try_resolve(OnboardingRegistry)
    if reg is None:
        reg = OnboardingRegistry()
        request.app.state.lifecycle.platform.container.register_instance(OnboardingRegistry, reg)
    return reg


# Deployment packs
@router.get("/packs")
async def list_packs(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [p.model_dump(mode="json") for p in _pack_reg(request).list_for_tenant(tenant_id)]


@router.post("/packs")
async def create_pack(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.deployment_packs.models import DeploymentPack
    pack = DeploymentPack(
        name=str(body.get("name", "Untitled Pack")),
        version=str(body.get("version", "1.0.0")),
        industry=str(body.get("industry", "general")),
        base_pack_id=str(body.get("base_pack_id", "")),
        artifacts=list(body.get("artifacts", [])),
        agents=list(body.get("agents", [])),
        workflows=list(body.get("workflows", [])),
        missions=list(body.get("missions", [])),
        policies=list(body.get("policies", [])),
        connectors=list(body.get("connectors", [])),
        dashboards=list(body.get("dashboards", [])),
        kpis=list(body.get("kpis", [])),
        methodologies=list(body.get("methodologies", [])),
        simulations=list(body.get("simulations", [])),
        terminology=dict(body.get("terminology", {})),
        governance=dict(body.get("governance", {})),
        onboarding_state=dict(body.get("onboarding_state", {})),
        tenant_id=tenant_id,
    )
    _pack_reg(request).create(pack)
    return pack.model_dump(mode="json")


@router.get("/packs/{pack_id}")
async def get_pack(request: Request, pack_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    p = _pack_reg(request).get(pack_id, tenant_id)
    if not p:
        raise HTTPException(status_code=404, detail="deployment pack not found")
    return p.model_dump(mode="json")


@router.delete("/packs/{pack_id}")
async def delete_pack(request: Request, pack_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ok = _pack_reg(request).delete(pack_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="deployment pack not found")
    return {"status": "deleted", "pack_id": pack_id}


# Deployment configs
@router.get("/configs")
async def list_configs(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [c.model_dump(mode="json") for c in _cfg_reg(request).list_for_tenant(tenant_id)]


@router.post("/configs")
async def create_config(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.deployment_packs.models import DeploymentConfig
    cfg = DeploymentConfig(
        tenant_id=tenant_id,
        environment=str(body.get("environment", "development")),
        region=str(body.get("region", "us-east-1")),
        runtime=str(body.get("runtime", "local-1")),
        model_policy=dict(body.get("model_policy", {})),
        connector_policy=dict(body.get("connector_policy", {})),
        autonomy_policy=dict(body.get("autonomy_policy", {})),
        governance_policy=dict(body.get("governance_policy", {})),
        industry_config=dict(body.get("industry_config", {})),
        deployment_version=str(body.get("deployment_version", "1.0.0")),
    )
    _cfg_reg(request).create(cfg)
    return cfg.model_dump(mode="json")


@router.get("/configs/{config_id}")
async def get_config(request: Request, config_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    c = _cfg_reg(request).get(config_id, tenant_id)
    if not c:
        raise HTTPException(status_code=404, detail="config not found")
    return c.model_dump(mode="json")


@router.post("/configs/{config_id}/validate")
async def validate_config(request: Request, config_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return _cfg_reg(request).validate(config_id, tenant_id).model_dump(mode="json")


# Onboarding — extended
@router.get("/onboarding")
async def list_onboarding(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [s.model_dump(mode="json") for s in _ob_reg(request).list_for_tenant(tenant_id)]


@router.post("/onboarding")
async def create_onboarding(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.deployment_packs.models import OnboardingSession
    sess = OnboardingSession(
        tenant_id=tenant_id,
        company_name=str(body.get("company_name", body.get("company", ""))),
        industry=str(body.get("industry", "")),
        requirements=dict(body.get("requirements", {})),
        solution_pack_id=str(body.get("solution_pack_id", body.get("pack_id", ""))),
    )
    _ob_reg(request).create(sess)
    return sess.model_dump(mode="json")


@router.get("/onboarding/{session_id}")
async def get_onboarding(request: Request, session_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    s = _ob_reg(request).get(session_id, tenant_id)
    if not s:
        raise HTTPException(status_code=404, detail="onboarding session not found")
    return s.model_dump(mode="json")


@router.post("/onboarding/{session_id}/advance")
async def advance_onboarding(request: Request, session_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    data = body or {}
    step = str(data.pop("step", data.pop("current_step", ""))) if data else ""
    s = _ob_reg(request).advance(session_id, tenant_id, step, data)
    if not s:
        raise HTTPException(status_code=404, detail="onboarding session not found")
    return s.model_dump(mode="json")
