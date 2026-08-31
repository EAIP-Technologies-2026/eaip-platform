"""Data models for emergency access management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EmergencyRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class EmergencyRequest(BaseModel):
    """A request for emergency access to a resource."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    requester_id: str
    resource: str
    reason: str
    justification: str = Field(default="")
    duration_minutes: int = Field(default=30, ge=1)
    status: EmergencyRequestStatus = Field(default=EmergencyRequestStatus.PENDING)
    requested_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(default_factory=utc_now)


class EmergencyApproval(BaseModel):
    """An approval or rejection of an emergency access request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    request_id: str
    approver_id: str
    action: str
    comment: str = Field(default="")
    decided_at: datetime = Field(default_factory=utc_now)


class EmergencyConfig(BaseModel):
    """Configuration for the emergency access manager."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_duration_minutes: int = Field(default=240, ge=1)
    require_justification: bool = Field(default=True)
    auto_expire_minutes: int = Field(default=60, ge=1)


__all__ = [
    "EmergencyApproval",
    "EmergencyConfig",
    "EmergencyRequest",
    "EmergencyRequestStatus",
]
