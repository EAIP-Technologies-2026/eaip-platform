"""Copilot domain models — risk tiers, approvals, and conversation turns."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RiskTier(StrEnum):
    """How much risk a governed tool invocation carries."""

    INFORMATIONAL = "informational"
    ACTION = "action"
    DESTRUCTIVE = "destructive"


class ApprovalStatus(StrEnum):
    """Lifecycle of a Conductor approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConductorContext(BaseModel):
    """Contextual metadata passed with a Conductor request."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    current_route: str = "/"
    application: str = "enterprise_console"
    entity_id: str | None = None
    entity_type: str | None = None
    active_tab: str | None = None
    selected_ids: tuple[str, ...] = Field(default_factory=tuple)
    session_id: str | None = None
    page_context: dict[str, Any] = Field(default_factory=dict)


class ConductorChatRequest(BaseModel):
    """Request body for a single Conductor turn."""

    model_config = ConfigDict(extra="ignore")

    message: str
    conversation_id: str | None = None
    context: ConductorContext | None = None
    response_format: dict[str, Any] | None = None


class ApprovalRequest(BaseModel):
    """A request for human approval before a governed tool executes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    requester_id: str
    risk: RiskTier = RiskTier.ACTION
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = None
    decided_by: str | None = None
    result: str | None = None


class ToolEvent(BaseModel):
    """A single governed tool invocation that happened during a turn."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool_name: str
    status: str
    summary: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)
    audit_entry_id: str | None = None


class CopilotTurn(BaseModel):
    """The complete outcome of one Conductor turn."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    reply: str
    tool_events: tuple[ToolEvent, ...] = Field(default_factory=tuple)
    pending_approval: ApprovalRequest | None = None
    conversation_id: str | None = None
    correlation_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "ApprovalRequest",
    "ApprovalStatus",
    "ConductorChatRequest",
    "ConductorContext",
    "CopilotTurn",
    "RiskTier",
    "ToolEvent",
]
