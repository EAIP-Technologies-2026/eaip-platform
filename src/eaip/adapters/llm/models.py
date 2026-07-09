"""LLMAdapter models — LLMRequest, LLMResponse, RunContext."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.providers.models import ChatMessage, ToolCall
from eaip.shared.time import utc_now


class LLMRequest(BaseModel):
    """High-level request to an LLM adapter.

    Differs from ``ChatRequest`` in that ``tools`` are resolved by name
    through the adapter's ``ToolRegistry`` rather than carrying inline
    ``ToolDefinition`` schemas.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str
    messages: tuple[ChatMessage, ...]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    tools: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Tool names to make available to the LLM.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """High-level response from an LLM adapter.

    Includes metadata about the tool-calling round count in addition to
    what a standard ``ChatResponse`` carries.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str
    provider: str
    adapter: str = ""
    content: str
    finish_reason: str = "stop"
    tool_calls: tuple[ToolCall, ...] | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    rounds: int = 1
    timestamp: datetime = Field(default_factory=utc_now)


class RunContext(BaseModel):
    """Runtime context propagated through an LLMAdapter completion call.

    Carries tenant, tracing, and execution metadata so adapters and tool
    orchestrators can observe and isolate their work.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str = ""
    run_id: str = ""
    correlation_id: str = ""
    labels: dict[str, str] = Field(default_factory=dict)
    max_tool_rounds: int = Field(
        default=10,
        description="Maximum number of tool-calling rounds before forcing a final response.",
    )


__all__ = ["LLMRequest", "LLMResponse", "RunContext"]
