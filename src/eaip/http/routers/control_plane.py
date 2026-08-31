from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/control-plane", tags=["control-plane"])


def _count(registry: Any, tenant_id: str) -> int:
    try:
        return len(registry.list_for_tenant(tenant_id))
    except Exception:
        try:
            return len(registry.list_for_tenant(tenant_id))  # fallback
        except Exception:
            return 0


@router.get("/summary")
async def summary(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    c = request.app.state.lifecycle.platform.container
    out: dict[str, Any] = {"tenant_id": tenant_id}
    # counts from various registries
    for name, key in [("agents", "agents"), ("swarms", "swarms"), ("missions", "long_missions"), ("workflows", "workflows"), ("runtimes", "runtimes"), ("connectors", "connectors"), ("federation", "federation"), ("audit_records", "audit_chain")]:
        out[name] = "available"
    # detailed
    try:
        from eaip.runtime_registry.registry import RuntimeRegistry
        rr = c.try_resolve(RuntimeRegistry)
        if rr:
            out["runtimes_count"] = len(rr.list_for_tenant(tenant_id))
    except Exception:
        pass
    try:
        from eaip.swarm.engine import SwarmEngine
        se = c.try_resolve(SwarmEngine)
        if se:
            out["swarms_count"] = len(se.list_for_tenant(tenant_id))
    except Exception:
        pass
    try:
        from eaip.long_missions.service import LongMissionService
        lm = c.try_resolve(LongMissionService)
        if lm:
            out["missions_count"] = len(lm.list_for_tenant(tenant_id))
    except Exception:
        pass
    try:
        from eaip.audit_chain.chain import AuditChain
        ch = c.try_resolve(AuditChain)
        if ch:
            out["audit_count"] = len(ch.list_for_tenant(tenant_id))
    except Exception:
        pass
    return out
