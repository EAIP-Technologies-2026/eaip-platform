"""Data models for consent and privacy management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ConsentStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ConsentPurpose(StrEnum):
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    SHARING = "sharing"
    RESEARCH = "research"


class DataSubjectRequestType(StrEnum):
    ACCESS = "access"
    DELETION = "deletion"
    PORTABILITY = "portability"
    RECTIFICATION = "rectification"
    RESTRICTION = "restriction"


class DataSubjectRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConsentRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    subject_id: str
    purpose: ConsentPurpose
    status: ConsentStatus = Field(default=ConsentStatus.ACTIVE)
    granted_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PrivacyPreference(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str
    data_categories: tuple[str, ...] = Field(default=())
    processing_purposes: tuple[ConsentPurpose, ...] = Field(default=())
    opt_out_marketing: bool = Field(default=False)
    opt_out_analytics: bool = Field(default=False)
    data_retention_days: int = Field(default=365, ge=0)
    updated_at: datetime = Field(default_factory=utc_now)


class DataSubjectRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    subject_id: str
    request_type: DataSubjectRequestType
    status: DataSubjectRequestStatus = Field(default=DataSubjectRequestStatus.PENDING)
    description: str = Field(default="")
    submitted_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    response_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ConsentPurpose",
    "ConsentRecord",
    "ConsentStatus",
    "DataSubjectRequest",
    "DataSubjectRequestStatus",
    "DataSubjectRequestType",
    "PrivacyPreference",
]
