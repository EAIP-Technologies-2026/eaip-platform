from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class OnboardingStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class OnboardingSession(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    tenant_id: str
    company_name: str
    industry: str = ""
    pack_id: str = ""
    status: OnboardingStatus = OnboardingStatus.pending
    progress: int = 0
    steps: tuple[str, ...] = Field(default_factory=tuple)
    current_step: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
