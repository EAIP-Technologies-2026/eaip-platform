from __future__ import annotations

import asyncio
from typing import Any


class ConnectorAdapter:
    def __init__(self, server_id: str, tenant_id: str, category: str, tools: list[str]) -> None:
        self.server_id = server_id
        self.tenant_id = tenant_id
        self.category = category
        self.tools = tools

    async def invoke(self, tool: str, args: dict[str, Any], timeout_s: float = 10) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        if tool not in self.tools:
            raise ValueError(f"tool {tool!r} not in adapter {self.category}")
        return {"category": self.category, "tool": tool, "tenant_id": self.tenant_id, "result": f"mock:{tool}", "args": args}


ADAPTERS: dict[str, ConnectorAdapter] = {}


def get_or_create(category: str, tenant_id: str) -> ConnectorAdapter:
    key = f"{tenant_id}:{category}"
    if key in ADAPTERS:
        return ADAPTERS[key]
    mapping = {
        "erp": ["orders", "inventory", "suppliers", "finance_refs"],
        "crm": ["customers", "opportunities", "cases"],
        "scada": ["telemetry", "alarms", "equipment_state"],
        "ehr": ["appointments", "care_ops", "compliance_data"],
    }
    tools = mapping.get(category, ["generic"])
    ad = ConnectorAdapter(server_id=f"{category}-{tenant_id[:6]}", tenant_id=tenant_id, category=category, tools=tools)
    ADAPTERS[key] = ad
    return ad


__all__ = ["ConnectorAdapter", "get_or_create"]
