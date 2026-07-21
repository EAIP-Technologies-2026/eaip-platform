"""Webhook domain models — endpoint, delivery, secret, receipt, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EndpointStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookEndpoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    url: str
    secret: str | None = None
    events: tuple[str, ...] = Field(default=())
    headers: dict[str, str] = Field(default_factory=dict)
    retry_config: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 60
    enabled: bool = True
    status: EndpointStatus = EndpointStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebhookDelivery(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    endpoint_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempt: int = 1
    max_attempts: int = 3
    last_attempt_at: datetime | None = None
    delivered_at: datetime | None = None
    response_status_code: int | None = None
    response_body: str | None = None
    duration_ms: float | None = None
    error: str | None = None
    next_retry_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebhookSecret(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    endpoint_id: str
    key: str
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeliveryReceipt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    delivery_id: str
    endpoint_id: str
    status: DeliveryStatus
    timestamp: datetime = Field(default_factory=utc_now)
    headers_sent: dict[str, str] = Field(default_factory=dict)
    response_summary: dict[str, Any] = Field(default_factory=dict)
    checksum: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebhookConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_max_attempts: int = 3
    default_retry_delay_seconds: int = 60
    backoff_multiplier: float = 2.0
    max_backoff_seconds: int = 3600
    signature_header_name: str = "X-Signature-256"
    default_timeout_seconds: int = 30
    max_concurrent_deliveries: int = 10
    delivery_retention_days: int = 30
    enable_delivery_tracking: bool = True


__all__ = [
    "DeliveryReceipt",
    "DeliveryStatus",
    "EndpointStatus",
    "WebhookConfig",
    "WebhookDelivery",
    "WebhookEndpoint",
    "WebhookSecret",
]
