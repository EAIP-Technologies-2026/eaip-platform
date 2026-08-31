from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from eaip.http.dependencies import get_current_user, get_tenant_id
from eaip.logging.context import get_logger
from eaip.mcp.models import MCPServerRecord, MCPServerStatus, MCPTransportType
from eaip.mcp.registry import MCPServerRegistry, MCPToolRegistry

router = APIRouter(prefix="/integrations", tags=["integrations"])
log = get_logger("eaip.http.routers.integrations")


def _servers(req: Request) -> MCPServerRegistry:
    reg = req.app.state.lifecycle.platform.container.try_resolve(MCPServerRegistry)
    if reg is None:
        reg = MCPServerRegistry()
        req.app.state.lifecycle.platform.container.register_instance(MCPServerRegistry, reg)
    return reg


def _tools(req: Request) -> MCPToolRegistry:
    reg = req.app.state.lifecycle.platform.container.try_resolve(MCPToolRegistry)
    if reg is None:
        reg = MCPToolRegistry()
        req.app.state.lifecycle.platform.container.register_instance(MCPToolRegistry, reg)
    return reg


def _record_to_dict(r: MCPServerRecord) -> dict[str, Any]:
    return {
        "server_id": r.server_id,
        "tenant_id": r.tenant_id,
        "name": r.name,
        "transport_type": r.transport_type.value,
        "endpoint": r.endpoint,
        "command": r.command,
        "args": list(r.args),
        "status": r.status.value,
        "capabilities": list(r.capabilities),
        "version": r.version,
        "permissions": list(r.permissions),
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
        "metadata": r.metadata,
    }


@router.get("/servers")
async def list_servers(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return [_record_to_dict(r) for r in _servers(request).list_for_tenant(tenant_id)]


@router.post("/servers")
async def create_server(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _servers(request)
    name = str(body.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    server_id = str(body.get("server_id") or body.get("serverId") or f"mcp-{uuid.uuid4().hex[:8]}")
    ttype = str(body.get("transport_type") or body.get("transportType") or "stdio")
    try:
        transport_type = MCPTransportType(ttype)
    except ValueError:
        transport_type = MCPTransportType.stdio
    record = MCPServerRecord(
        server_id=server_id,
        tenant_id=tenant_id,
        name=name,
        transport_type=transport_type,
        endpoint=str(body.get("endpoint", "")),
        command=str(body.get("command", "")),
        args=tuple(body.get("args", [])),
        status=MCPServerStatus.draft,
        capabilities=tuple(body.get("capabilities", [])),
        version=str(body.get("version", "1.0.0")),
        permissions=tuple(body.get("permissions", [])),
        metadata=body.get("metadata") or {},
    )
    reg.register(record)
    log.info("integrations.server.registered", server_id=server_id, tenant_id=tenant_id)
    return _record_to_dict(record)


@router.get("/servers/{server_id}")
async def get_server(request: Request, server_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _servers(request).get(server_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="server not found")
    return _record_to_dict(rec)


@router.put("/servers/{server_id}")
async def update_server(request: Request, server_id: str, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _servers(request)
    existing = reg.get(server_id, tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="server not found")
    patch: dict[str, Any] = {}
    for k in ("name", "endpoint", "command", "version"):
        if k in body:
            patch[k] = body[k]
    for k in ("capabilities", "permissions", "args"):
        if k in body:
            patch[k] = tuple(body[k]) if isinstance(body[k], list) else body[k]
    if "metadata" in body:
        patch["metadata"] = body["metadata"]
    updated = reg.update(server_id, tenant_id, patch)
    if not updated:
        raise HTTPException(status_code=404, detail="server not found")
    return _record_to_dict(updated)


@router.delete("/servers/{server_id}")
async def delete_server(request: Request, server_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    ok = _servers(request).delete(server_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="server not found")
    return {"status": "deleted", "server_id": server_id}


@router.post("/servers/{server_id}/connect")
async def connect_server(request: Request, server_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _servers(request)
    rec = reg.get(server_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="server not found")
    if rec.status == MCPServerStatus.disabled:
        raise HTTPException(status_code=400, detail="server is disabled")
    reg.set_status(server_id, tenant_id, MCPServerStatus.connected)
    log.info("integrations.server.connected", server_id=server_id, tenant_id=tenant_id)
    return {"status": "connected", "server_id": server_id}


@router.post("/servers/{server_id}/disconnect")
async def disconnect_server(request: Request, server_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _servers(request)
    rec = reg.get(server_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="server not found")
    reg.set_status(server_id, tenant_id, MCPServerStatus.disconnected)
    return {"status": "disconnected", "server_id": server_id}


@router.get("/health")
async def integrations_health(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _servers(request)
    summary = reg.health_summary(tenant_id) if hasattr(reg, "health_summary") else {}
    total = sum(summary.values()) if summary else len(reg.list_for_tenant(tenant_id))
    return {"tenant_id": tenant_id, "total_servers": total, "by_status": summary, "status": "healthy" if total else "empty"}


@router.post("/servers/{server_id}/health")
async def health_server(request: Request, server_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _servers(request).get(server_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="server not found")
    return {"server_id": server_id, "status": rec.status.value, "connected": rec.status == MCPServerStatus.connected}


@router.post("/servers/{server_id}/enable")
async def enable_server(request: Request, server_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _servers(request)
    rec = reg.get(server_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="server not found")
    reg.set_status(server_id, tenant_id, MCPServerStatus.disconnected)
    return {"status": "enabled", "server_id": server_id}


@router.post("/servers/{server_id}/disable")
async def disable_server(request: Request, server_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    reg = _servers(request)
    rec = reg.get(server_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="server not found")
    reg.set_status(server_id, tenant_id, MCPServerStatus.disabled)
    return {"status": "disabled", "server_id": server_id}


@router.get("/servers/{server_id}/tools")
async def list_server_tools(request: Request, server_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    rec = _servers(request).get(server_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="server not found")
    tools = _tools(request).list_for_server(server_id, tenant_id)
    return [{"name": t.name, "description": t.description, "server_id": t.server_id, "availability": t.availability, "version": t.version} for t in tools]


@router.post("/servers/{server_id}/tools/{tool_name}/invoke")
async def invoke_tool(request: Request, server_id: str, tool_name: str, body: dict[str, Any] | None = None, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    rec = _servers(request).get(server_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="server not found")
    from eaip.mcp.executor import MCPToolExecutor

    executor = request.app.state.lifecycle.platform.container.try_resolve(MCPToolExecutor)
    if executor:
        try:
            args = body.get("arguments") if isinstance(body, dict) and "arguments" in body else (body or {})
            result = await executor.invoke(tool_name, server_id, tenant_id, args if isinstance(args, dict) else {})
            return {"tool": tool_name, "server_id": server_id, "result": result}
        except Exception as exc:
            code = getattr(exc, "code", "ERROR")
            raise HTTPException(status_code=400, detail=f"{code}: {exc}") from exc
    from eaip.mcp.synthetic import MockTransport

    transport = MockTransport(server_id, tenant_id)
    args2 = body.get("arguments") if isinstance(body, dict) and "arguments" in body else (body or {})
    result2 = await transport.call_tool(tool_name, args2 if isinstance(args2, dict) else {})
    return {"tool": tool_name, "server_id": server_id, "result": result2}


@router.get("/tools")
async def list_all_tools(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    tools = _tools(request).list_for_tenant(tenant_id)
    return [{"name": t.name, "description": t.description, "server_id": t.server_id, "availability": t.availability} for t in tools]


@router.post("/credentials")
async def create_credential(request: Request, body: dict[str, Any], tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.mcp.credentials import CredentialStore

    store = request.app.state.lifecycle.platform.container.try_resolve(CredentialStore)
    if not store:
        store = CredentialStore()
        request.app.state.lifecycle.platform.container.register_instance(CredentialStore, store)
    credential_id = str(body.get("credential_id") or body.get("credentialId") or f"cred-{uuid.uuid4().hex[:8]}")
    ref = store.store(credential_id, tenant_id, credential_type=str(body.get("credential_type") or body.get("credentialType") or "api_key"), provider=str(body.get("provider", "")), reference=str(body.get("reference", f"vault://{tenant_id}/{credential_id}")))
    return {"credential_id": ref.credential_id, "tenant_id": ref.tenant_id, "credential_type": ref.credential_type, "provider": ref.provider, "reference": ref.reference, "created_at": ref.created_at.isoformat()}


@router.get("/credentials")
async def list_credentials(request: Request, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    from eaip.mcp.credentials import CredentialStore

    store = request.app.state.lifecycle.platform.container.try_resolve(CredentialStore)
    if not store:
        return []
    refs = store.list_for_tenant(tenant_id)
    return [{"credential_id": r.credential_id, "tenant_id": r.tenant_id, "credential_type": r.credential_type, "provider": r.provider, "reference": r.reference, "created_at": r.created_at.isoformat()} for r in refs]


@router.delete("/credentials/{credential_id}")
async def delete_credential(request: Request, credential_id: str, tenant_id: str = Depends(get_tenant_id), _user: dict = Depends(get_current_user)) -> dict[str, Any]:
    from eaip.mcp.credentials import CredentialStore

    store = request.app.state.lifecycle.platform.container.try_resolve(CredentialStore)
    if not store or not store.delete(credential_id, tenant_id):
        raise HTTPException(status_code=404, detail="credential not found")
    return {"status": "deleted", "credential_id": credential_id}
