"""Pydantic models for the connector management subsystem."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ConnectorType(StrEnum):
    """Supported connector types."""

    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    SOAP = "soap"
    EVENT = "event"
    STREAM = "stream"
    DATABASE = "database"
    CUSTOM = "custom"


class ConnectorStatus(StrEnum):
    """Operational status of a connector."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEGRADED = "degraded"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"


class AuthMethod(StrEnum):
    """Supported authentication methods for connectors."""

    NONE = "none"
    API_KEY = "api_key"
    BASIC = "basic"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    CERTIFICATE = "certificate"
    CUSTOM = "custom"


class ConnectorOperationType(StrEnum):
    """Types of operations a connector can perform."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SUBSCRIBE = "subscribe"
    EXECUTE = "execute"


class ConnectorAuthConfig(BaseModel):
    """Authentication configuration for a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    method: AuthMethod = Field(description="Authentication method")
    credentials: dict[str, Any] = Field(
        default_factory=dict, description="Credential key-value pairs"
    )
    token_endpoint: str | None = Field(default=None, description="OAuth2 token endpoint")
    scopes: list[str] = Field(default_factory=list, description="OAuth2 scopes")


class ConnectorEndpoint(BaseModel):
    """Endpoint definition for a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str = Field(description="Endpoint URL")
    method: str = Field(default="POST", description="HTTP method")
    headers: dict[str, str] = Field(default_factory=dict, description="Custom headers")
    timeout_seconds: int = Field(default=30, ge=1, description="Request timeout")


class ConnectorRateLimit(BaseModel):
    """Rate-limit configuration for a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_requests_per_second: int = Field(default=10, ge=1, description="Max requests per second")
    max_concurrent: int = Field(default=5, ge=1, description="Max concurrent requests")
    burst_size: int = Field(default=20, ge=1, description="Allowed burst size")


class ConnectorRetryPolicy(BaseModel):
    """Retry policy for connector operations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    base_delay_seconds: float = Field(default=1.0, ge=0, description="Base delay between retries")
    max_delay_seconds: float = Field(
        default=60.0, ge=0, description="Maximum delay between retries"
    )
    backoff_multiplier: float = Field(
        default=2.0, ge=1.0, description="Exponential backoff multiplier"
    )


class ConnectorSchema(BaseModel):
    """Schema definition for a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    input_schema: dict[str, Any] = Field(default_factory=dict, description="Input schema")
    output_schema: dict[str, Any] = Field(default_factory=dict, description="Output schema")
    version: str = Field(default="1.0.0", description="Schema version")


class ConnectorMetadata(BaseModel):
    """Metadata for a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Human-readable name")
    description: str = Field(default="", description="Description of the connector")
    version: str = Field(default="1.0.0", description="Connector version")
    tags: dict[str, str] = Field(default_factory=dict, description="Key-value tags")
    created_at: datetime = Field(
        default_factory=utc_now, description="When the connector was created"
    )
    updated_at: datetime = Field(
        default_factory=utc_now, description="When the connector was last updated"
    )


class ConnectorConfig(BaseModel):
    """Full configuration for a connector instance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique connector identifier")
    connector_type: ConnectorType = Field(description="Type of connector")
    status: ConnectorStatus = Field(default=ConnectorStatus.INACTIVE, description="Current status")
    metadata: ConnectorMetadata = Field(description="Connector metadata")
    auth: ConnectorAuthConfig = Field(description="Authentication configuration")
    endpoint: ConnectorEndpoint = Field(description="Endpoint configuration")
    schema_: ConnectorSchema = Field(
        default_factory=ConnectorSchema, alias="schema", description="Schema definition"
    )
    rate_limit: ConnectorRateLimit = Field(
        default_factory=ConnectorRateLimit, description="Rate-limit configuration"
    )
    retry_policy: ConnectorRetryPolicy = Field(
        default_factory=ConnectorRetryPolicy, description="Retry policy"
    )
    enabled: bool = Field(default=True, description="Whether the connector is enabled")


class ConnectorDefinition(BaseModel):
    """Blueprint for a connector type that can be instantiated."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: ConnectorType = Field(description="Connector type")
    metadata: ConnectorMetadata = Field(description="Default metadata")
    schema_: ConnectorSchema = Field(
        default_factory=ConnectorSchema, alias="schema", description="Default schema"
    )
    auth_methods: list[AuthMethod] = Field(description="Supported auth methods")
    operations: list[str] = Field(default_factory=list, description="Supported operation names")


class ConnectorHealthStatus(BaseModel):
    """Health status snapshot for a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connector_id: str = Field(description="Connector identifier")
    healthy: bool = Field(description="Whether the connector is healthy")
    status: ConnectorStatus = Field(description="Current operational status")
    message: str = Field(default="", description="Status message")
    latency_ms: float | None = Field(default=None, description="Measured latency")
    last_checked: datetime = Field(
        default_factory=utc_now, description="When the check was performed"
    )


class ConnectorSyncResult(BaseModel):
    """Result of a connector synchronization operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connector_id: str = Field(description="Connector identifier")
    success: bool = Field(description="Whether the sync succeeded")
    records_synced: int = Field(default=0, description="Number of records synchronized")
    errors: list[str] = Field(default_factory=list, description="Sync error messages")
    started_at: datetime = Field(description="When the sync started")
    completed_at: datetime = Field(description="When the sync completed")


class ConnectorMetrics(BaseModel):
    """Runtime metrics for a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connector_id: str = Field(description="Connector identifier")
    requests_total: int = Field(default=0, description="Total requests made")
    requests_succeeded: int = Field(default=0, description="Successful requests")
    requests_failed: int = Field(default=0, description="Failed requests")
    total_latency_ms: float = Field(default=0.0, description="Accumulated latency in milliseconds")
    last_request_at: datetime | None = Field(default=None, description="Timestamp of last request")


class ConnectorOperation(BaseModel):
    """An operation to be executed on a connector."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation_id: str = Field(description="Unique operation identifier")
    connector_id: str = Field(description="Target connector identifier")
    operation_type: ConnectorOperationType = Field(description="Type of operation")
    name: str = Field(description="Operation name")
    params: dict[str, Any] = Field(default_factory=dict, description="Operation parameters")


class ConnectorRegistryEntry(BaseModel):
    """Entry in the connector registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    connector_id: str = Field(description="Connector identifier")
    definition: ConnectorDefinition = Field(description="Connector definition")
    config: ConnectorConfig = Field(description="Connector configuration")
    health: ConnectorHealthStatus | None = Field(default=None, description="Latest health status")
    metrics: ConnectorMetrics | None = Field(default=None, description="Latest metrics")
    registered_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "AuthMethod",
    "ConnectorAuthConfig",
    "ConnectorConfig",
    "ConnectorDefinition",
    "ConnectorEndpoint",
    "ConnectorHealthStatus",
    "ConnectorMetadata",
    "ConnectorMetrics",
    "ConnectorOperation",
    "ConnectorOperationType",
    "ConnectorRateLimit",
    "ConnectorRegistryEntry",
    "ConnectorRetryPolicy",
    "ConnectorSchema",
    "ConnectorStatus",
    "ConnectorSyncResult",
    "ConnectorType",
]
