from __future__ import annotations

import asyncio
from typing import Any

from eaip.logging.context import get_logger
from eaip.mcp.registry import MCPServerRegistry, MCPToolRegistry
from eaip.mcp.transport import MCPToolError, MCPTransport

log = get_logger("eaip.mcp.executor")


class MCPExecutorError(Exception):
    def __init__(self, message: str, code: str = "EXECUTOR_ERROR") -> None:
        super().__init__(message)
        self.code = code


class MCPToolExecutor:
    def __init__(self, server_registry: MCPServerRegistry, tool_registry: MCPToolRegistry, event_bus: Any | None = None) -> None:
        self._servers = server_registry
        self._tools = tool_registry
        self._event_bus = event_bus
        self._transports: dict[str, MCPTransport] = {}

    def register_transport(self, server_id: str, tenant_id: str, transport: MCPTransport) -> None:
        self._transports[f"{tenant_id}:{server_id}"] = transport

    def get_transport(self, server_id: str, tenant_id: str) -> MCPTransport | None:
        return self._transports.get(f"{tenant_id}:{server_id}")

    def for_server(self, server_id: str, tenant_id: str) -> MCPTransport | None:
        return self.get_transport(server_id, tenant_id)

    async def invoke(self, tool_name: str, server_id: str, tenant_id: str, arguments: dict[str, Any], timeout_s: float = 30, retries: int = 2) -> dict[str, Any]:
        server = self._servers.get(server_id, tenant_id)
        if not server:
            raise MCPExecutorError(f"server {server_id!r} not found for tenant {tenant_id!r}", code="NOT_FOUND")
        tool = self._tools.get(server_id, tenant_id, tool_name)
        if not tool:
            available = [t.name for t in self._tools.list_for_server(server_id, tenant_id)]
            raise MCPExecutorError(f"tool {tool_name!r} not available (have: {available})", code="NOT_FOUND")
        if not tool.availability:
            raise MCPExecutorError(f"tool {tool_name!r} disabled", code="DISABLED")
        transport = self._transports.get(f"{tenant_id}:{server_id}")
        if not transport:
            raise MCPExecutorError(f"no transport for {server_id!r}", code="NO_TRANSPORT")
        self._publish("integration.tool_started", {"server_id": server_id, "tenant_id": tenant_id, "tool": tool_name})
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                result = await asyncio.wait_for(transport.call_tool(tool_name, arguments, timeout_s=timeout_s), timeout=timeout_s + 2)
                self._publish("integration.tool_completed", {"server_id": server_id, "tenant_id": tenant_id, "tool": tool_name})
                return result if isinstance(result, dict) else {"result": result}
            except asyncio.TimeoutError as exc:
                last_exc = MCPToolError(f"tool {tool_name!r} timed out", code="TIMEOUT", server_id=server_id)
                if attempt < retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
            except MCPToolError as exc:
                last_exc = exc
                if attempt < retries and exc.code in ("TIMEOUT", "TRANSIENT"):
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                break
            except Exception as exc:
                last_exc = MCPToolError(str(exc), server_id=server_id)
                break
        assert last_exc is not None
        self._publish("integration.tool_failed", {"server_id": server_id, "tenant_id": tenant_id, "tool": tool_name, "error": str(last_exc)})
        raise last_exc

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
