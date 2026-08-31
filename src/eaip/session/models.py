"""Session & context models — enterprise session state, context scopes, propagation config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SessionStatus(StrEnum):
    """Lifecycle status of a session."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CLOSED = "closed"


class SessionType(StrEnum):
    """Classifications for sessions."""

    USER = "user"
    WORKFLOW = "workflow"
    AGENT = "agent"
    SYSTEM = "system"


class ContextScope(StrEnum):
    """Scope levels for context propagation."""

    ENTERPRISE = "enterprise"
    TENANT = "tenant"
    USER = "user"
    WORKFLOW = "workflow"
    AGENT = "agent"
    EXECUTION = "execution"


class Session(BaseModel):
    """An enterprise session carrying identity, lifecycle, and context snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: SessionType = SessionType.USER
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    ttl_seconds: int | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    workflow_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: tuple[str, ...] = Field(default=())
    parent_session_id: str | None = None
    context_snapshot: dict[str, Any] = Field(default_factory=dict)


class SessionContext(BaseModel):
    """A lightweight context payload attached to a running session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    correlation_id: str | None = None
    tenant_id: str | None = None
    user_id: str | None = None
    workflow_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ContextPropagationConfig(BaseModel):
    """Configuration for how context propagates across session boundaries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    propagate_to_children: bool = True
    propagate_to_agents: bool = False
    propagate_to_workflows: bool = True
    max_depth: int = 5
    allowed_attributes: list[str] = Field(default_factory=list)


class SessionConfig(BaseModel):
    """Configuration for session management behaviour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    default_ttl_seconds: int = 3600
    max_sessions_per_user: int = 100
    enable_auto_expiry: bool = True
    enable_persistence: bool = False


class ExecutionContext(BaseModel):
    """A scoped execution node within a session's context tree."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    session_id: str
    parent_id: str | None = None
    scope: ContextScope = ContextScope.EXECUTION
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "ContextPropagationConfig",
    "ContextScope",
    "ExecutionContext",
    "Session",
    "SessionConfig",
    "SessionContext",
    "SessionStatus",
    "SessionType",
]
