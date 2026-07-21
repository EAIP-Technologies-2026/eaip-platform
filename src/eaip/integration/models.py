"""Integration domain models — connectors, messages, routes, transformations, webhooks, and config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ConnectorDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: str  # http / webhook / mq / grpc / custom
    endpoint_url: str
    auth_config: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    max_retries: int = 3
    timeout_seconds: int = 30


class IntegrationMessage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source: str
    destination: str
    headers: dict[str, str] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    content_type: str = "application/json"
    correlation_id: str = ""
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageRoute(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source_pattern: str
    destination_pattern: str
    transformation_ids: tuple[str, ...] = Field(default=())
    enabled: bool = True
    priority: int = 0
    error_handling: str = "discard"  # discard / retry / dead_letter
    filter_expression: str = ""


class Transformation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: str  # mapping / filter / enrich / script
    config: dict[str, Any] = Field(default_factory=dict)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class WebhookRegistration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    url: str
    secret: str = ""
    events: tuple[str, ...] = Field(default=())
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    last_called_at: datetime | None = None
    call_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntegrationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_message_size_bytes: int = 1_048_576  # 1 MB
    default_timeout_seconds: int = 30
    max_retries: int = 3
    enable_dead_letter: bool = True
    dead_letter_retention_days: int = 7
    enable_audit_logging: bool = True


__all__ = [
    "ConnectorDefinition",
    "IntegrationConfig",
    "IntegrationMessage",
    "MessageRoute",
    "Transformation",
    "WebhookRegistration",
]
