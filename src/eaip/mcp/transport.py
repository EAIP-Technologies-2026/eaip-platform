from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any


class MCPToolError(Exception):
    def __init__(self, message: str, code: str = "MCP_ERROR", server_id: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.server_id = server_id


class MCPTransport(ABC):
    def __init__(self, server_id: str, tenant_id: str) -> None:
        self.server_id = server_id
        self.tenant_id = tenant_id
        self._connected = False

    @abstractmethod
    async def connect(self, timeout_s: float = 10) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def list_tools(self, timeout_s: float = 10) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def call_tool(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]: ...

    @abstractmethod
    async def health(self) -> dict[str, Any]: ...

    def is_connected(self) -> bool:
        return self._connected

    async def discover(self, timeout_s: float = 10) -> list[dict[str, Any]]:
        return await self.list_tools(timeout_s=timeout_s)

    async def invoke(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]:
        return await self.call_tool(name, arguments, timeout_s=timeout_s)

    async def cancel(self) -> None:
        await self.disconnect()


class StdioTransport(MCPTransport):
    def __init__(self, server_id: str, tenant_id: str, command: str = "", args: tuple[str, ...] = ()) -> None:
        super().__init__(server_id, tenant_id)
        self.command = command
        self.args = args
        self._proc: asyncio.subprocess.Process | None = None
        self._mock = command == "mock" or not command

    async def connect(self, timeout_s: float = 10) -> None:
        if self._mock:
            self._connected = True
            return
        try:
            self._proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    self.command,
                    *self.args,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=timeout_s,
            )
            await self._rpc("initialize", {"protocolVersion": "2024-11-05"}, timeout_s=timeout_s)
            self._connected = True
        except asyncio.TimeoutError as exc:
            raise MCPToolError(f"stdio connect timeout for {self.server_id}", code="TIMEOUT", server_id=self.server_id) from exc

    async def disconnect(self) -> None:
        self._connected = False
        if self._proc:
            try:
                self._proc.terminate()
                await asyncio.wait_for(self._proc.wait(), timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    async def list_tools(self, timeout_s: float = 10) -> list[dict[str, Any]]:
        if self._mock:
            return []
        result = await self._rpc("tools/list", {}, timeout_s=timeout_s)
        return result.get("tools", []) if isinstance(result, dict) else []

    async def call_tool(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]:
        if self._mock:
            return {"mock": True, "tool": name, "arguments": arguments}
        return await self._rpc("tools/call", {"name": name, "arguments": arguments}, timeout_s=timeout_s)

    async def health(self) -> dict[str, Any]:
        return {"connected": self._connected, "transport": "stdio", "server_id": self.server_id}

    async def discover(self, timeout_s: float = 10) -> list[dict[str, Any]]:
        return await self.list_tools(timeout_s=timeout_s)

    async def invoke(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]:
        return await self.call_tool(name, arguments, timeout_s=timeout_s)

    async def cancel(self) -> None:
        await self.disconnect()

    async def _rpc(self, method: str, params: dict[str, Any], timeout_s: float = 10) -> Any:
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            raise MCPToolError("stdio transport not connected", server_id=self.server_id)
        msg = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}) + "\n"
        assert self._proc.stdin is not None
        self._proc.stdin.write(msg.encode())
        await self._proc.stdin.drain()
        assert self._proc.stdout is not None
        line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=timeout_s)
        if not line:
            raise MCPToolError("stdio transport closed", server_id=self.server_id)
        resp = json.loads(line.decode())
        if "error" in resp:
            raise MCPToolError(str(resp["error"]), server_id=self.server_id)
        return resp.get("result", {})


class HTTPTransport(MCPTransport):
    def __init__(self, server_id: str, tenant_id: str, url: str = "", headers: dict[str, str] | None = None) -> None:
        super().__init__(server_id, tenant_id)
        self.url = url
        self.headers = headers or {}
        self._mock = not url or url.startswith("mock:")

    async def connect(self, timeout_s: float = 10) -> None:
        if self._mock:
            self._connected = True
            return
        import httpx

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(f"{self.url}/initialize", json={"protocolVersion": "2024-11-05"}, headers=self.headers)
            resp.raise_for_status()
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def list_tools(self, timeout_s: float = 10) -> list[dict[str, Any]]:
        if self._mock:
            return []
        import httpx

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.get(f"{self.url}/tools", headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("tools", []) if isinstance(data, dict) else []

    async def call_tool(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]:
        if self._mock:
            return {"mock": True, "tool": name, "arguments": arguments}
        import httpx

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(f"{self.url}/tools/{name}/invoke", json=arguments, headers=self.headers)
            resp.raise_for_status()
            return resp.json() if resp.content else {}

    async def health(self) -> dict[str, Any]:
        if self._mock:
            return {"connected": self._connected, "transport": "http", "mock": True}
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.url}/health", headers=self.headers)
                return {"connected": resp.status_code == 200, "status": resp.status_code}
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    async def discover(self, timeout_s: float = 10) -> list[dict[str, Any]]:
        return await self.list_tools(timeout_s=timeout_s)

    async def invoke(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]:
        return await self.call_tool(name, arguments, timeout_s=timeout_s)

    async def cancel(self) -> None:
        await self.disconnect()


class SSETransport(MCPTransport):
    def __init__(self, server_id: str, tenant_id: str, url: str = "", headers: dict[str, str] | None = None) -> None:
        super().__init__(server_id, tenant_id)
        self.url = url
        self.headers = headers or {}
        self._mock = not url or url.startswith("mock:")
        self._connected_at: float | None = None

    async def connect(self, timeout_s: float = 10) -> None:
        if self._mock:
            self._connected = True
            return
        import httpx
        import time
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.get(f"{self.url}/sse", headers={**self.headers, "Accept": "text/event-stream"})
            if resp.status_code not in (200, 204):
                resp.raise_for_status()
            self._connected = True
            self._connected_at = time.monotonic()

    async def disconnect(self) -> None:
        self._connected = False
        self._connected_at = None

    async def list_tools(self, timeout_s: float = 10) -> list[dict[str, Any]]:
        if self._mock:
            return []
        import httpx
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.get(f"{self.url}/tools", headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("tools", []) if isinstance(data, dict) else []

    async def call_tool(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]:
        if self._mock:
            return {"mock": True, "tool": name, "arguments": arguments, "transport": "sse"}
        import httpx
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.post(f"{self.url}/tools/{name}/invoke", json=arguments, headers=self.headers)
            resp.raise_for_status()
            return resp.json() if resp.content else {}

    async def health(self) -> dict[str, Any]:
        if self._mock:
            return {"connected": self._connected, "transport": "sse", "mock": True}
        if not self._connected:
            return {"connected": False, "transport": "sse"}
        import time
        uptime = (time.monotonic() - self._connected_at) if self._connected_at else 0
        return {"connected": True, "transport": "sse", "uptime_s": uptime}

    async def discover(self, timeout_s: float = 10) -> list[dict[str, Any]]:
        return await self.list_tools(timeout_s=timeout_s)

    async def invoke(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]:
        return await self.call_tool(name, arguments, timeout_s=timeout_s)

    async def cancel(self) -> None:
        await self.disconnect()
