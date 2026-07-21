"""Data models for the Administrative API."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ApiMethod(StrEnum):
    """HTTP method for an API endpoint."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ApiAuthScheme(StrEnum):
    """Authentication scheme for an API."""

    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    OPENID = "openid"


class ApiClientStatus(StrEnum):
    """Status of an API client."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class ApiVersionStatus(StrEnum):
    """Lifecycle status of an API version."""

    DRAFT = "draft"
    RELEASED = "released"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ApiDefinition(BaseModel):
    """A registered API definition managed through the admin API."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    base_path: str = ""
    version: str = "1.0.0"
    auth_scheme: ApiAuthScheme = ApiAuthScheme.API_KEY
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ApiVersion(BaseModel):
    """A versioned snapshot of an API definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    api_definition_id: str
    version_string: str
    status: ApiVersionStatus = ApiVersionStatus.DRAFT
    released_at: datetime | None = None
    deprecated_at: datetime | None = None
    retired_at: datetime | None = None
    changelog: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ApiEndpoint(BaseModel):
    """A single endpoint within an API version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    api_definition_id: str
    api_version_id: str
    path: str
    method: ApiMethod
    description: str = ""
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    auth_required: bool = True
    rate_limit: int = 100
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiRequest(BaseModel):
    """A record of an incoming API request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    endpoint_id: str
    method: ApiMethod
    path: str
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    client_ip: str = ""
    api_client_id: str | None = None


class ApiResponse(BaseModel):
    """A record of an API response sent back to a client."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    request_id: str
    status_code: int = 200
    headers: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    duration_ms: float = 0.0


class ApiRateLimit(BaseModel):
    """Rate limiting configuration for an API or endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    requests_per_second: int = 10
    burst_size: int = 20
    concurrent_limit: int = 50


class ApiThrottleConfig(BaseModel):
    """Global throttle configuration for the admin API."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    default_rate_limit: int = 100
    rate_limit_by_endpoint: dict[str, int] = Field(default_factory=dict)
    rate_limit_by_client: dict[str, int] = Field(default_factory=dict)
    burst_size: int = 50
    concurrent_limit: int = 100


class ApiUsageMetric(BaseModel):
    """Aggregated usage metrics for an API endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    endpoint_id: str
    api_client_id: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    request_count: int = 0
    response_count: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    status_code_counts: dict[str, int] = Field(default_factory=dict)
    bytes_sent: int = 0
    bytes_received: int = 0


class ApiAuditEntry(BaseModel):
    """An audit trail entry for an administrative API operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    timestamp: datetime = Field(default_factory=utc_now)
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    outcome: str = "success"
    correlation_id: str | None = None


class ApiClient(BaseModel):
    """A registered API client with credentials and permissions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = ""
    client_id: str
    status: ApiClientStatus = ApiClientStatus.ACTIVE
    permissions: tuple[str, ...] = Field(default=())
    rate_limit_config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_used_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiClientPermission(BaseModel):
    """A permission grant for an API client on a specific endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    client_id: str
    endpoint_id: str
    permission: str = "read"
    granted_at: datetime = Field(default_factory=utc_now)
    granted_by: str = "system"


class ApiClientToken(BaseModel):
    """An issued token for an API client."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    client_id: str
    token_prefix: str
    token_hash: str
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class ApiDocumentation(BaseModel):
    """Generated documentation for an API definition or version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    api_definition_id: str
    api_version_id: str
    format: str = "markdown"
    content: str = ""
    generated_at: datetime = Field(default_factory=utc_now)
    version: str = "1.0.0"


class ApiSpecification(BaseModel):
    """An API specification (e.g. OpenAPI, Swagger) for a definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    api_definition_id: str
    api_version_id: str
    format: str = "openapi-3.1"
    content: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)
    specification_type: str = "openapi"


class ApiHealthEndpoint(BaseModel):
    """A health check endpoint for an API definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    api_definition_id: str
    path: str = "/health"
    method: ApiMethod = ApiMethod.GET
    expected_status_code: int = 200
    timeout_ms: int = 5000


class ApiSwaggerConfig(BaseModel):
    """Swagger / OpenAPI UI configuration for an API definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    title: str = "API Documentation"
    description: str = ""
    version: str = "1.0.0"
    contact_email: str = ""
    license_name: str = ""
    license_url: str = ""
    servers: tuple[str, ...] = Field(default=())


__all__ = [
    "ApiAuditEntry",
    "ApiAuthScheme",
    "ApiClient",
    "ApiClientPermission",
    "ApiClientStatus",
    "ApiClientToken",
    "ApiDefinition",
    "ApiDocumentation",
    "ApiEndpoint",
    "ApiHealthEndpoint",
    "ApiMethod",
    "ApiRateLimit",
    "ApiRequest",
    "ApiResponse",
    "ApiSpecification",
    "ApiSwaggerConfig",
    "ApiThrottleConfig",
    "ApiUsageMetric",
    "ApiVersion",
    "ApiVersionStatus",
]
