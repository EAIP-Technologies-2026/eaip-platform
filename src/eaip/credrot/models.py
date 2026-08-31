"""Credential rotation models — credentials, schedules, config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class CredRotStatus(StrEnum):
    ACTIVE = "active"
    ROTATING = "rotating"
    ROTATED = "rotated"
    REVOKED = "revoked"


class Credential(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: str
    status: CredRotStatus = Field(default=CredRotStatus.ACTIVE)
    last_rotated_at: datetime | None = None
    rotation_frequency_days: int = Field(default=90)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RotationSchedule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    credential_id: str
    scheduled_at: datetime
    executed_at: datetime | None = None
    status: CredRotStatus = Field(default=CredRotStatus.ACTIVE)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CredRotConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_frequency_days: int = Field(default=90)
    auto_rotate: bool = Field(default=True)
    notify_before_days: int = Field(default=7)
    max_rotation_retries: int = Field(default=3)
