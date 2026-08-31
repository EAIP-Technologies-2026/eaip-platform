from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.marketplace.models import MarketplacePackage, PackageStatus, PackageType
from eaip.marketplace.trusted_registry import TrustedMarketplace

router = APIRouter(prefix="/marketplace-trusted", tags=["marketplace-trusted"])


def _trusted(req: Request) -> TrustedMarketplace:
    t = req.app.state.lifecycle.platform.container.try_resolve(TrustedMarketplace)
    if t is None:
        t = TrustedMarketplace()
        req.app.state.lifecycle.platform.container.register_instance(TrustedMarketplace, t)
    return t


@router.post("/publish", status_code=201)
async def publish_trusted(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    pkg = MarketplacePackage(package_id=body.get("package_id") or f"pkg-{uuid.uuid4().hex[:8]}", name=name, type=PackageType(body.get("type", "tool")) if body.get("type") in [e.value for e in PackageType] else PackageType.TOOL, version=str(body.get("version", "1.0.0")), description=str(body.get("description", "")), author=str(_user.get("sub", "unknown")), status=PackageStatus.PUBLISHED)
    rec = _trusted(request).publish(pkg, tenant_id=tenant_id)
    return {"package_id": pkg.package_id, "signature": rec["signature"], "status": rec["status"]}


@router.get("/packages")
async def list_trusted(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _trusted(request).list_for_tenant(tenant_id)


@router.get("/packages/{package_id}/verify")
async def verify_trusted(request: Request, package_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    result = _trusted(request).verify(package_id)
    if not result.get("valid") and result.get("reason") == "not found":
        raise HTTPException(status_code=404, detail="package not found")
    return result


@router.post("/packages/{package_id}/revoke")
async def revoke_trusted(request: Request, package_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ok = _trusted(request).revoke(package_id)
    if not ok:
        raise HTTPException(status_code=404, detail="package not found")
    return {"status": "revoked", "package_id": package_id}


@router.post("/packages/{package_id}/install")
async def install_trusted(request: Request, package_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    t = _trusted(request)
    rec = t.get(package_id)
    if not rec:
        raise HTTPException(status_code=404, detail="package not found")
    v = t.verify(package_id)
    if not v.get("valid"):
        raise HTTPException(status_code=400, detail="invalid signature — rejected")
    if rec.get("revoked"):
        raise HTTPException(status_code=400, detail="package revoked")
    return {"status": "installed", "package_id": package_id, "verified": True}
