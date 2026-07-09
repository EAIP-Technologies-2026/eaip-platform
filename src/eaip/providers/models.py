"""Provider models — status, capability, chat types, tool calling."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import JsonSchemaValue

from eaip.shared.time import utc_now


class ProviderStatus(StrEnum):
    """Operational status of an AI provider."""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ModelFeature(StrEnum):
    """Features a model may support."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    STREAMING = "streaming"
    TOOL_USE = "tool_use"
    VISION = "vision"


class ModelCapability(BaseModel):
    """Describes a model offered by a provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_id: str
    provider: str
    features: tuple[ModelFeature, ...] = (ModelFeature.CHAT,)
    max_tokens: int = 4096
    context_window: int = 8192
    cost_per_token: float = 0.0


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: str
    content: str


class ChatRequest(BaseModel):
    """A request to send to an AI provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str
    messages: tuple[ChatMessage, ...]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    tools: tuple[ToolDefinition, ...] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """A response from an AI provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str
    provider: str
    content: str
    finish_reason: str = "stop"
    tool_calls: tuple[ToolCall, ...] | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=utc_now)


class ProviderInstance(BaseModel):
    """A registered provider instance with its configuration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    provider_type: str
    endpoint: str
    api_key: str = ""
    default_model: str = ""
    models: tuple[ModelCapability, ...] = ()
    status: ProviderStatus = ProviderStatus.UNAVAILABLE
    priority: int = 0
    timeout_seconds: float = 30.0
    metadata: dict[str, str] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    """Schema for a tool that an LLM may call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    parameters: JsonSchemaValue = Field(default_factory=dict)


class ToolCall(BaseModel):
    """A tool invocation request from the LLM."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result of executing a tool call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool_call_id: str
    content: str
    is_error: bool = False


__all__ = [
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "ModelCapability",
    "ModelFeature",
    "ProviderInstance",
    "ProviderStatus",
    "ToolCall",
    "ToolDefinition",
    "ToolResult",
]
