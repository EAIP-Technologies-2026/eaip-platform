from __future__ import annotations

import asyncio
import random
from typing import Any

from eaip.mcp.models import MCPServerRecord, MCPToolDefinition, MCPTransportType

SYNTHETIC_DEFS: list[dict[str, Any]] = [
    {"server_id": "apex-crm", "tenant_id": "apex-advisory-group", "name": "Apex CRM", "tools": ["list_opportunities", "create_task", "search_documents"], "enterprise": "apex"},
    {"server_id": "apex-projects", "tenant_id": "apex-advisory-group", "name": "Apex Projects", "tools": ["list_projects", "create_project", "update_status"], "enterprise": "apex"},
    {"server_id": "apex-docs", "tenant_id": "apex-advisory-group", "name": "Apex Docs", "tools": ["search_documents", "get_document", "create_document"], "enterprise": "apex"},
    {"server_id": "nova-erp", "tenant_id": "nova-manufacturing-systems", "name": "Nova ERP", "tools": ["list_orders", "create_order", "check_inventory"], "enterprise": "nova"},
    {"server_id": "nova-inventory", "tenant_id": "nova-manufacturing-systems", "name": "Nova Inventory", "tools": ["check_inventory", "update_inventory", "list_items"], "enterprise": "nova"},
    {"server_id": "nova-production", "tenant_id": "nova-manufacturing-systems", "name": "Nova Production", "tools": ["get_production_backlog", "create_work_order", "update_work_order"], "enterprise": "nova"},
    {"server_id": "meridian-compliance", "tenant_id": "meridian-health-services", "name": "Meridian Compliance", "tools": ["search_documents", "list_audits", "create_audit"], "enterprise": "meridian"},
    {"server_id": "meridian-scheduling", "tenant_id": "meridian-health-services", "name": "Meridian Scheduling", "tools": ["list_appointments", "create_appointment", "check_availability"], "enterprise": "meridian"},
    {"server_id": "meridian-records", "tenant_id": "meridian-health-services", "name": "Meridian Records", "tools": ["search_records", "get_record", "create_record"], "enterprise": "meridian"},
]


class MockTransport:
    def __init__(self, server_id: str, tenant_id: str, failure_rate: float = 0.05, latency_ms: int = 30) -> None:
        self.server_id = server_id
        self.tenant_id = tenant_id
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self._connected = True
        self._rng = random.Random(hash(server_id) % 10000)

    async def connect(self, timeout_s: float = 10) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def list_tools(self, timeout_s: float = 10) -> list[dict[str, Any]]:
        for d in SYNTHETIC_DEFS:
            if d["server_id"] == self.server_id:
                return [{"name": t, "description": f"Mock tool {t}", "inputSchema": {"type": "object", "properties": {}}, "version": "1.0.0"} for t in d["tools"]]
        return []

    async def call_tool(self, name: str, arguments: dict[str, Any], timeout_s: float = 30) -> dict[str, Any]:
        await asyncio.sleep(self.latency_ms / 1000)
        if self._rng.random() < self.failure_rate:
            from eaip.mcp.transport import MCPToolError
            raise MCPToolError(f"synthetic failure for {name}", code="TRANSIENT", server_id=self.server_id)
        return _mock_result(self.server_id, name, arguments)

    async def health(self) -> dict[str, Any]:
        return {"connected": self._connected, "transport": "mock", "server_id": self.server_id}


def _mock_result(server_id: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool == "list_opportunities":
        return {"opportunities": [{"id": f"opp-{i}", "name": f"Opportunity {i}", "value": 50000 + i * 10000, "stage": "proposal"} for i in range(1, 4)]}
    if tool == "create_task":
        return {"task_id": f"task-{random.randint(1000, 9999)}", "status": "created", "title": args.get("title", "Untitled")}
    if tool == "search_documents":
        q = args.get("query", args.get("q", "general"))
        return {"results": [{"id": f"doc-{i}", "title": f"Document {i} for {q}", "score": 0.9 - i * 0.1} for i in range(1, 4)], "query": q}
    if tool == "list_projects":
        return {"projects": [{"id": f"proj-{i}", "name": f"Project {i}", "status": "active"} for i in range(1, 4)]}
    if tool == "check_inventory":
        return {"items": [{"sku": f"SKU-{i}", "qty": 100 + i * 10, "available": True} for i in range(1, 4)]}
    if tool == "get_production_backlog":
        return {"backlog": [{"id": f"wo-{i}", "title": f"Work Order {i}", "priority": "high"} for i in range(1, 4)]}
    if tool == "search_records":
        return {"records": [{"id": f"rec-{i}", "type": "synthetic", "status": "active"} for i in range(1, 4)]}
    return {"tool": tool, "server_id": server_id, "arguments": args, "result": "ok", "mock": True}


def create_synthetic_servers() -> list[MCPServerRecord]:
    records: list[MCPServerRecord] = []
    for d in SYNTHETIC_DEFS:
        records.append(MCPServerRecord(
            server_id=d["server_id"],
            tenant_id=d["tenant_id"],
            name=d["name"],
            transport_type=MCPTransportType.stdio,
            command="mock",
            args=(),
            status="connected",
            capabilities=tuple(d["tools"]),
            version="1.0.0",
            permissions=("mcp:read", "mcp:invoke"),
            metadata={"enterprise": d["enterprise"], "synthetic": True},
        ))
    return records


def create_synthetic_tools() -> list[MCPToolDefinition]:
    tools: list[MCPToolDefinition] = []
    for d in SYNTHETIC_DEFS:
        for t in d["tools"]:
            tools.append(MCPToolDefinition(name=t, description=f"Mock {t} for {d['name']}", input_schema={"type": "object", "properties": {}}, server_id=d["server_id"], tenant_id=d["tenant_id"], permissions=("mcp:read",), availability=True))
    return tools
