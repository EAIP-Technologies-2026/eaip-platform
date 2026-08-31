"""Cross-region replication models — rules, status, config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ReplicationRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source_region: str
    target_region: str
    resource_type: str
    sync_interval_seconds: int = Field(default=300)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReplicationStatus(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    last_sync_at: datetime | None = None
    items_synced: int = Field(default=0)
    items_failed: int = Field(default=0)
    status: str = Field(default="idle")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReplicationConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_retries: int = Field(default=3)
    retry_delay_seconds: int = Field(default=30)
    batch_size: int = Field(default=100)
    enable_metrics: bool = Field(default=True)
