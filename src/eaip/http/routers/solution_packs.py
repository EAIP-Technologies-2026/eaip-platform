from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/solution-packs", tags=["solution-packs"])


def _registry(req: Request):
    from eaip.solution_packs.registry import SolutionPackRegistry
    reg = req.app.state.lifecycle.platform.container.try_resolve(SolutionPackRegistry)
    if reg is None:
        reg = SolutionPackRegistry()
        req.app.state.lifecycle.platform.container.register_instance(SolutionPackRegistry, reg)
    return reg


@router.get("")
async def list_packs(request: Request, _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    from eaip.solution_packs.catalog import list_packs
    return [p.model_dump(mode="json") for p in list_packs()]


@router.get("/{pack_id}")
async def get_pack(request: Request, pack_id: str, _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.solution_packs.catalog import get_pack
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="pack not found")
    return pack.model_dump(mode="json")


@router.post("/{pack_id}/install")
async def install_pack(request: Request, pack_id: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _registry(request)
    try:
        inst = reg.install(pack_id, tenant_id, config=body or {})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return inst.model_dump(mode="json")


@router.get("/installations/list")
async def list_installations(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    reg = _registry(request)
    return [i.model_dump(mode="json") for i in reg.list_for_tenant(tenant_id)]


@router.delete("/{pack_id}/install")
async def uninstall_pack(request: Request, pack_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _registry(request)
    ok = reg.uninstall(pack_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="installation not found")
    return {"status": "uninstalled", "pack_id": pack_id}
