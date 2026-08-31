"""MCP Pydantic Models."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class McpServerManifest(BaseModel):
    id: str = Field(..., description="Unique server ID")
    name: str = Field(..., description="Human readable name")
    command: str = Field(..., description="Command to execute")
    args: list[str] = Field(default_factory=list)
    description: str = Field("", description="Server description")
    version: str = Field("1.0.0", description="Server version")


class ToolSpec(BaseModel):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict[str, Any] = Field(..., description="JSON Schema of parameters")


class ToolResult(BaseModel):
    content: str = Field(..., description="Text output of the tool")
    is_error: bool = Field(default=False, description="Whether the execution failed")


class McpAuditEntry(BaseModel):
    correlation_id: str
    action: str
    server_id: str
    tool_name: str | None = None
    principal: str | None = None
    args_hash: str | None = None
    result_hash: str | None = None
    duration_ms: float | None = None
    status: str
    error: str | None = None
