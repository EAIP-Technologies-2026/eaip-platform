"""Data models for the EAIP API Gateway."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now


class HttpMethod(StrEnum):
    """HTTP methods supported by the gateway."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class RateLimitConfig(BaseModel):
    """Rate-limit configuration for an endpoint or API key."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_requests: int = Field(gt=0, description="Max requests allowed in the window.")
    window_seconds: float = Field(gt=0, description="Sliding window duration.")


class Endpoint(BaseModel):
    """A registered API endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(description="URL path pattern.")
    method: HttpMethod = Field(description="HTTP method.")
    description: str = Field(default="", description="Human-readable description.")
    tags: tuple[str, ...] = Field(default=(), description="Categorisation tags.")
    handler: Callable[[Any], Coroutine[Any, Any, Any]] = Field(
        description="Async handler accepting an ApiRequest.",
        exclude=True,
    )
    auth_required: bool = Field(default=True, description="Whether auth is required.")
    rate_limit_config: RateLimitConfig | None = Field(
        default=None,
        description="Per-endpoint rate-limit override.",
    )


class ApiRequest(BaseModel):
    """An incoming API request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique request identifier.")
    method: HttpMethod = Field(description="HTTP method.")
    path: str = Field(description="Request path.")
    headers: dict[str, str] = Field(default_factory=dict, description="Request headers.")
    query_params: dict[str, str] = Field(
        default_factory=dict,
        description="Query-string parameters.",
    )
    body: Any = Field(default=None, description="Request body.")
    timestamp: datetime = Field(default_factory=utc_now, description="Arrival timestamp.")
    correlation_id: CorrelationId | None = Field(
        default=None,
        description="Correlation / tracing token.",
    )
    subject_id: str | None = Field(
        default=None,
        description="Authenticated subject (e.g. API key name).",
    )


class ApiResponse(BaseModel):
    """An outgoing API response."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(description="Echo of the originating request ID.")
    status_code: int = Field(default=200, description="HTTP status code.")
    headers: dict[str, str] = Field(default_factory=dict, description="Response headers.")
    body: Any = Field(default=None, description="Response body.")
    duration_ms: float = Field(
        default=0.0,
        description="Processing duration in milliseconds.",
    )


class ApiKeyCredentials(BaseModel):
    """Stored credentials for an API key."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key_id: str = Field(description="Unique key identifier.")
    name: str = Field(description="Human-readable key name.")
    roles: tuple[str, ...] = Field(default=(), description="Roles assigned to this key.")
    enabled: bool = Field(default=True, description="Whether the key is active.")


__all__ = [
    "ApiKeyCredentials",
    "ApiRequest",
    "ApiResponse",
    "Endpoint",
    "HttpMethod",
    "RateLimitConfig",
]
