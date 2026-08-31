"""Data models for the data retention and purge service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PurgeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PolicyScope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str
    identifiers: tuple[str, ...] = Field(default=())


class RetentionPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    data_type: str = Field(default="*")
    retention_days: int = Field(default=90, ge=1)
    scope: PolicyScope | None = Field(default=None)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PurgeJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    policy_id: str
    status: PurgeStatus = Field(default=PurgeStatus.PENDING)
    total_items: int = Field(default=0, ge=0)
    purged_items: int = Field(default=0, ge=0)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_message: str = Field(default="")


class RetentionConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_purge_batch_size: int = Field(default=1000, ge=1)
    schedule_interval_minutes: int = Field(default=1440, ge=1)


__all__ = [
    "PolicyScope",
    "PurgeJob",
    "PurgeStatus",
    "RetentionConfig",
    "RetentionPolicy",
]
