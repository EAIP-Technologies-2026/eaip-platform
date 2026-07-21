"""Pydantic models for the message queue subsystem."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class QueueMessage(BaseModel):
    """A single message travelling through the queue."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    message_id: str
    payload: bytes
    content_type: str = "application/octet-stream"
    correlation_id: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    retry_count: int = 0
    max_retries: int = 3


class QueueConfig(BaseModel):
    """Configuration for a single queue instance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    max_size: int = 10000
    visibility_timeout_seconds: int = 30
    delivery_delay_seconds: int = 0
    dead_letter_queue: str | None = None
    max_receive_count: int = 3


class QueueStats(BaseModel):
    """Snapshot of queue metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_enqueued: int = 0
    total_dequeued: int = 0
    total_failed: int = 0
    current_depth: int = 0
    dead_letter_depth: int = 0


class QueueSubscription(BaseModel):
    """A handler subscription bound to a queue."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subscription_id: str
    queue_name: str
    handler_type: str
    filter_pattern: str | None = None
    active: bool = True
