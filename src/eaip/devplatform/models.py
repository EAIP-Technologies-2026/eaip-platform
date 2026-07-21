"""Data models for the Developer API & SDK Platform."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class VersionStatus(StrEnum):
    """Lifecycle status of an API version."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


class ParameterLocation(StrEnum):
    """Location of an API parameter."""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    BODY = "body"


class DeveloperProfileStatus(StrEnum):
    """Status of a developer profile."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


class ApiVersion(BaseModel):
    """A versioned snapshot of the public API contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    version_string: str
    status: VersionStatus = VersionStatus.ACTIVE
    released_at: datetime = Field(default_factory=utc_now)
    sunset_at: datetime | None = None
    changelog: str = ""
    migration_guide: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiParameter(BaseModel):
    """A single parameter accepted by an API endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: str
    location: ParameterLocation
    required: bool = False
    description: str = ""
    default: Any = None
    json_schema: dict[str, Any] = Field(default_factory=dict)


class ApiEndpoint(BaseModel):
    """A registered public API endpoint with versioning and metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    path: str
    method: str
    version: str
    description: str = ""
    parameters: tuple[ApiParameter, ...] = Field(default=())
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    auth_required: bool = True
    rate_limit: int = 100
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeveloperKey(BaseModel):
    """A developer API key with permissions and rate limiting."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    key_prefix: str
    key_hash: str
    developer_id: str
    permissions: tuple[str, ...] = Field(default=())
    rate_limit_config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UsageRecord(BaseModel):
    """A single API usage record for analytics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    developer_id: str
    api_version: str
    endpoint: str
    timestamp: datetime = Field(default_factory=utc_now)
    response_time_ms: float = 0.0
    status_code: int = 200
    bytes_sent: int = 0
    bytes_received: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeveloperProfile(BaseModel):
    """A developer profile with keys and application metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    email: str
    organization: str = ""
    keys: tuple[str, ...] = Field(default=())
    applications: tuple[str, ...] = Field(default=())
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: DeveloperProfileStatus = DeveloperProfileStatus.ACTIVE


class PlaygroundSession(BaseModel):
    """A developer playground session for testing API endpoints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    developer_id: str
    endpoint_id: str
    request_preview: dict[str, Any] = Field(default_factory=dict)
    response_preview: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    last_activity: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SdkConfig(BaseModel):
    """Configuration settings for the SDK platform behaviour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    default_rate_limit: int = 100
    max_keys_per_developer: int = 10
    key_expiry_days: int = 365
    enable_playground: bool = True
    playground_timeout_minutes: int = 30
    usage_retention_days: int = 90
    enable_analytics: bool = True


__all__ = [
    "ApiEndpoint",
    "ApiParameter",
    "ApiVersion",
    "DeveloperKey",
    "DeveloperProfile",
    "DeveloperProfileStatus",
    "ParameterLocation",
    "PlaygroundSession",
    "SdkConfig",
    "UsageRecord",
    "VersionStatus",
]
