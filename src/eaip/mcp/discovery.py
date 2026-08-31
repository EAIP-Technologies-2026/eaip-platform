from __future__ import annotations

import asyncio
from typing import Any

from eaip.logging.context import get_logger
from eaip.mcp.models import MCPToolDefinition
from eaip.mcp.registry import MCPServerRegistry, MCPToolRegistry
from eaip.mcp.transport import MCPTransport

log = get_logger("eaip.mcp.discovery")


class MCPDiscoveryService:
    def __init__(self, server_registry: MCPServerRegistry, tool_registry: MCPToolRegistry, event_bus: Any | None = None) -> None:
        self._servers = server_registry
        self._tools = tool_registry
        self._event_bus = event_bus
        self._transports: dict[str, MCPTransport] = {}

    def register_transport(self, server_id: str, tenant_id: str, transport: MCPTransport) -> None:
        self._transports[f"{tenant_id}:{server_id}"] = transport

    async def discover_tools(self, server_id: str, tenant_id: str, timeout_s: float = 10) -> list[MCPToolDefinition]:
        transport = self._transports.get(f"{tenant_id}:{server_id}")
        server = self._servers.get(server_id, tenant_id)
        if not server:
            return []
        raw_tools: list[dict[str, Any]] = []
        if transport:
            try:
                raw_tools = await asyncio.wait_for(transport.list_tools(timeout_s=timeout_s), timeout=timeout_s + 2)
            except asyncio.TimeoutError:
                log.warning("mcp.discover.timeout", server_id=server_id)
            except Exception as exc:
                log.warning("mcp.discover.failed", server_id=server_id, error=str(exc))
        defs: list[MCPToolDefinition] = []
        for t in raw_tools:
            try:
                defs.append(MCPToolDefinition(
                    name=str(t.get("name", "")),
                    description=str(t.get("description", "")),
                    input_schema=t.get("inputSchema") or t.get("input_schema") or {},
                    server_id=server_id,
                    tenant_id=tenant_id,
                    permissions=tuple(t.get("permissions", [])),
                    availability=True,
                    version=str(t.get("version", "1.0.0")),
                ))
            except Exception:
                continue
        if not defs and server:
            for cap in server.capabilities:
                defs.append(MCPToolDefinition(name=cap, description=f"Tool {cap} from {server.name}", server_id=server_id, tenant_id=tenant_id))
        self._tools.discover(server_id, tenant_id, defs)
        self._publish("integration.tool_discovered", {"server_id": server_id, "tenant_id": tenant_id, "count": len(defs)})
        return defs

    async def sync_all_for_tenant(self, tenant_id: str, timeout_s: float = 10) -> int:
        total = 0
        for srv in self._servers.list_for_tenant(tenant_id):
            tools = await self.discover_tools(srv.server_id, tenant_id, timeout_s=timeout_s)
            total += len(tools)
        return total

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            evt = {"type": event_type, **payload}
            result = self._event_bus.publish(evt)
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception:
            pass
