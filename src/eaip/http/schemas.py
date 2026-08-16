"""Standardized API contract schemas for EAIP Platform.

These Pydantic models define the canonical request/response shapes used across
all EAIP HTTP routers.  They enforce:

- Consistent error responses (RFC 7807-inspired)
- Consistent pagination envelopes
- Consistent status/action acknowledgements
- Typed request bodies for validation and OpenAPI generation

Existing routers that return raw ``dict[str, Any]`` are NOT forcibly migrated
in this batch.  New endpoints and contract-tested endpoints MUST use these
schemas.  Migration of existing endpoints happens organically as routers are
touched for B03 integration.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Error responses
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Structured error detail following RFC 7807 Problem Details (simplified)."""

    model_config = {"frozen": True, "extra": "forbid"}

    type: str = Field(default="about:blank", description="URI reference for the error type")
    title: str = Field(description="Short human-readable summary")
    status: int = Field(description="HTTP status code")
    detail: str = Field(default="", description="Human-readable explanation")
    instance: str = Field(default="", description="URI reference to the specific occurrence")
    code: str = Field(default="", description="Application-specific error code")


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all EAIP endpoints."""

    model_config = {"frozen": True, "extra": "forbid"}

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginationParams(BaseModel):
    """Standard query parameters for paginated list endpoints."""

    model_config = {"frozen": True, "extra": "forbid"}

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    pageSize: int = Field(default=20, ge=1, le=200, alias="pageSize", description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination envelope for list endpoints."""

    model_config = {"frozen": True, "extra": "forbid"}

    data: list[T] = Field(description="List of items for the current page")
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number")
    pageSize: int = Field(description="Items per page")
    totalPages: int = Field(description="Total number of pages")


# ---------------------------------------------------------------------------
# Status / action acknowledgements
# ---------------------------------------------------------------------------


class StatusResponse(BaseModel):
    """Generic status acknowledgement (e.g. delete, archive, pause)."""

    model_config = {"frozen": True, "extra": "forbid"}

    status: str = Field(default="ok", description="Operation status")
    message: str = Field(default="", description="Optional human-readable message")


class IdResponse(BaseModel):
    """Response containing a resource identifier."""

    model_config = {"frozen": True, "extra": "forbid"}

    id: str = Field(description="Resource identifier")
    status: str = Field(default="ok", description="Operation status")


# ---------------------------------------------------------------------------
# Auth request/response schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """Login request body."""

    model_config = {"frozen": True, "extra": "forbid"}

    username: str = Field(description="Username or email")
    password: str = Field(description="Password")


class LoginResponse(BaseModel):
    """Login success response."""

    model_config = {"frozen": True, "extra": "forbid"}

    token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="Refresh token for obtaining new access tokens")
    user: UserSummary = Field(description="Authenticated user summary")


class RefreshRequest(BaseModel):
    """Token refresh request body."""

    model_config = {"frozen": True, "extra": "forbid"}

    refresh_token: str = Field(description="Refresh token")


class RefreshResponse(BaseModel):
    """Token refresh success response."""

    model_config = {"frozen": True, "extra": "forbid"}

    token: str = Field(description="New JWT access token")
    refresh_token: str = Field(description="New refresh token")


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------


class UserSummary(BaseModel):
    """Minimal user representation returned by auth endpoints."""

    model_config = {"frozen": True, "extra": "forbid"}

    id: str = Field(description="User identifier")
    name: str = Field(default="", description="Display name")
    email: str = Field(default="", description="Email address")
    roles: list[str] = Field(default_factory=list, description="Assigned roles")


# ---------------------------------------------------------------------------
# Agent schemas
# ---------------------------------------------------------------------------


class AgentSummary(BaseModel):
    """Agent list-item representation."""

    model_config = {"frozen": True, "extra": "forbid"}

    id: str
    name: str
    description: str = ""
    status: str = "idle"
    model: str = "default"
    labels: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    owner: str = ""
    createdAt: str = ""
    updatedAt: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)


class AgentDetail(BaseModel):
    """Full agent representation."""

    model_config = {"frozen": True, "extra": "forbid"}

    id: str
    name: str
    description: str = ""
    status: str = "idle"
    model: str = "default"
    systemPrompt: str = ""
    tools: list[dict[str, Any]] = Field(default_factory=list)
    knowledge: list[Any] = Field(default_factory=list)
    memory: list[Any] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    labels: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    owner: str = ""
    createdAt: str = ""
    updatedAt: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Workflow schemas
# ---------------------------------------------------------------------------


class WorkflowSummary(BaseModel):
    """Workflow list-item representation."""

    model_config = {"frozen": True, "extra": "forbid"}

    id: str
    name: str
    description: str = ""
    status: str = "draft"
    triggers: str = "0"
    labels: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    owner: str = ""
    createdAt: str = ""
    updatedAt: str = ""


# ---------------------------------------------------------------------------
# Brain schemas
# ---------------------------------------------------------------------------


class BrainSummary(BaseModel):
    """Brain list-item representation."""

    model_config = {"frozen": True, "extra": "forbid"}

    id: str
    name: str
    description: str = ""
    template: str = ""
    status: str = "active"
    owner: str = ""
    organizationId: str = ""
    createdAt: str = ""
    updatedAt: str = ""


# ---------------------------------------------------------------------------
# Health check schemas
# ---------------------------------------------------------------------------


class HealthCheckResult(BaseModel):
    """Individual health check result."""

    model_config = {"frozen": True, "extra": "forbid"}

    component: str
    status: str
    message: str = ""
    criticality: str | None = None
    configured: bool = True


class HealthResponse(BaseModel):
    """System health response."""

    model_config = {"frozen": True, "extra": "forbid"}

    status: str
    message: str = ""
    checks: list[HealthCheckResult] = Field(default_factory=list)
    background_tasks: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# OpenAPI metadata
# ---------------------------------------------------------------------------

API_TITLE = "EAIP Platform"
API_DESCRIPTION = (
    "Enterprise AI Platform — unified API for agents, workflows, knowledge, "
    "brains, missions, marketplace, and enterprise intelligence."
)
API_VERSION = "1.0.0"
API_CONTACT = {"name": "EAIP Engineering", "url": "https://github.com/eaip-platform"}
API_LICENSE = {"name": "Proprietary", "url": "https://eaip-platform.com/license"}


__all__ = [
    "API_CONTACT",
    "API_DESCRIPTION",
    "API_LICENSE",
    "API_TITLE",
    "API_VERSION",
    "AgentDetail",
    "AgentSummary",
    "BrainSummary",
    "ErrorDetail",
    "ErrorResponse",
    "HealthCheckResult",
    "HealthResponse",
    "IdResponse",
    "LoginRequest",
    "LoginResponse",
    "PaginatedResponse",
    "PaginationParams",
    "RefreshRequest",
    "RefreshResponse",
    "StatusResponse",
    "UserSummary",
    "WorkflowSummary",
]
