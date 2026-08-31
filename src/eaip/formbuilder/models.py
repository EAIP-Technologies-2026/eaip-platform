"""Data models for form builder service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class FormStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SubmissionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class FormDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    form_schema: dict[str, object] = Field(default_factory=dict)
    fields: tuple[str, ...] = Field(default=())
    validation_rules: dict[str, object] = Field(default_factory=dict)
    status: FormStatus = Field(default=FormStatus.DRAFT)


class FormSubmission(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    form_id: str
    data: dict[str, object] = Field(default_factory=dict)
    submitted_by: str
    submitted_at: datetime = Field(default_factory=utc_now)
    status: SubmissionStatus = Field(default=SubmissionStatus.PENDING)


class FormConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_fields_per_form: int = Field(default=100, ge=1)
    max_submissions_per_user: int = Field(default=1000, ge=1)
    enable_draft_autosave: bool = Field(default=True)
    default_form_status: FormStatus = Field(default=FormStatus.DRAFT)


__all__ = [
    "FormConfig",
    "FormDefinition",
    "FormStatus",
    "FormSubmission",
    "SubmissionStatus",
]
