"""Pydantic models for the cross-platform connector bridge."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ProtocolType(StrEnum):
    """Supported connector protocols."""

    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    SOAP = "soap"
    EVENT = "event"


class ConnectorConfig(BaseModel):
    """Configuration for a connector endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for this connector")
    name: str = Field(description="Human-readable name of the connector")
    protocol: ProtocolType = Field(description="Protocol the connector uses")
    endpoint: str = Field(description="Endpoint URL for the connector")
    auth_config: dict[str, Any] = Field(
        default_factory=dict, description="Authentication configuration"
    )
    timeout_seconds: int = Field(default=30, ge=1, description="Request timeout in seconds")
    retry_policy: dict[str, Any] = Field(
        default_factory=dict, description="Retry policy configuration"
    )


class MessageEnvelope(BaseModel):
    """A message envelope for cross-platform communication."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for this message")
    source: str = Field(description="Source connector ID")
    target: str = Field(description="Target connector ID")
    payload: dict[str, Any] = Field(description="Message payload")
    content_type: str = Field(default="application/json", description="Content type of the payload")
    correlation_id: str | None = Field(default=None, description="Correlation ID for tracing")
    timestamp: datetime = Field(default_factory=utc_now, description="When the message was created")


class BridgeRoute(BaseModel):
    """A route defining how messages flow between connectors."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for this route")
    source: str = Field(description="Source connector ID")
    target: str = Field(description="Target connector ID")
    transform: str | None = Field(default=None, description="Optional transformation to apply")
    enabled: bool = Field(default=True, description="Whether this route is active")


class BridgeConfig(BaseModel):
    """Configuration for the connector bridge."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_message_size_bytes: int = Field(
        default=10 * 1024 * 1024, ge=1, description="Maximum message size in bytes"
    )
    default_timeout_seconds: int = Field(
        default=30, ge=1, description="Default timeout for message delivery"
    )
    enable_message_logging: bool = Field(default=True, description="Whether to log messages")
    history_retention_days: int = Field(
        default=30, ge=1, description="Days to retain message history"
    )


__all__ = [
    "BridgeConfig",
    "BridgeRoute",
    "ConnectorConfig",
    "MessageEnvelope",
    "ProtocolType",
]
