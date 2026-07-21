"""SDK domain models — definitions, endpoints, clients, builds, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SdkStatus(StrEnum):
    """Lifecycle status of an SDK definition."""

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class ClientStatus(StrEnum):
    """Lifecycle status of an API client."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class BuildStatus(StrEnum):
    """Build progress states."""

    PENDING = "pending"
    BUILDING = "building"
    COMPLETED = "completed"
    FAILED = "failed"


class SdkDefinition(BaseModel):
    """A versioned SDK definition describing an API surface."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    language: str
    version: str
    description: str = ""
    source_api_version: str = ""
    endpoints: tuple[str, ...] = Field(default=())
    models: tuple[str, ...] = Field(default=())
    config: dict[str, Any] = Field(default_factory=dict)
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: SdkStatus = SdkStatus.DRAFT
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SdkEndpoint(BaseModel):
    """An endpoint exposed by an SDK."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    path: str
    method: str
    description: str = ""
    parameters: tuple[str, ...] = Field(default=())
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    auth_required: bool = True
    tags: tuple[str, ...] = Field(default=())


class ApiClient(BaseModel):
    """A registered API client consuming an SDK."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    sdk_id: str
    client_version: str = "1.0.0"
    status: ClientStatus = ClientStatus.ACTIVE
    api_key_id: str = ""
    configuration: dict[str, Any] = Field(default_factory=dict)
    last_used_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SdkBuild(BaseModel):
    """A build record for an SDK version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    sdk_id: str
    version: str
    status: BuildStatus = BuildStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
    artifact_url: str = ""
    artifact_size_bytes: int = 0
    error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class EndpointModel(BaseModel):
    """A data model definition used by an SDK endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    fields: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SdkConfig(BaseModel):
    """Configuration governing SDK behaviour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_clients_per_sdk: int = 100
    build_timeout_seconds: int = 300
    enable_auto_build: bool = True
    artifact_retention_days: int = 90
    supported_languages: tuple[str, ...] = Field(
        default=("python", "javascript", "java", "go", "dotnet"),
    )
    default_language: str = "python"
