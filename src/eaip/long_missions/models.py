from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class LongMissionStatus(StrEnum):
    pending = "pending"
    running = "running"
    paused = "paused"
    checkpointed = "checkpointed"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class MissionCheckpoint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    checkpoint_id: str
    mission_id: str
    tenant_id: str
    step_index: int
    state: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class LongMissionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mission_id: str
    tenant_id: str
    name: str
    status: LongMissionStatus = LongMissionStatus.pending
    steps: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    current_step: int = 0
    checkpoints: tuple[MissionCheckpoint, ...] = Field(default_factory=tuple)
    autonomy_level: str = "SUGGEST"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
