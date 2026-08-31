from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class MCPServerStatus(StrEnum):
    draft = "draft"
    connecting = "connecting"
    connected = "connected"
    disconnected = "disconnected"
    error = "error"
    disabled = "disabled"


class MCPTransportType(StrEnum):
    stdio = "stdio"
    http = "http"
    sse = "sse"


class MCPServerRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    server_id: str
    tenant_id: str
    name: str
    transport_type: MCPTransportType = MCPTransportType.stdio
    endpoint: str = ""
    command: str = ""
    args: tuple[str, ...] = Field(default_factory=tuple)
    status: MCPServerStatus = MCPServerStatus.draft
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    version: str = "1.0.0"
    permissions: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_health_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPToolDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    server_id: str
    tenant_id: str
    permissions: tuple[str, ...] = Field(default_factory=tuple)
    availability: bool = True
    version: str = "1.0.0"


class MCPCredentialRef(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    credential_id: str
    tenant_id: str
    credential_type: str = "api_key"
    provider: str = ""
    reference: str = ""
    created_at: datetime = Field(default_factory=utc_now)
