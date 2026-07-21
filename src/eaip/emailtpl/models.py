"""Data models for email template design."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TemplateStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EmailTemplate(BaseModel):
    """An email template with subject, body, and variable placeholders."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    subject: str
    body_html: str
    body_text: str
    variables: tuple[str, ...] = Field(default=())
    category: str = Field(default="general")
    version: int = Field(default=1, ge=1)
    status: TemplateStatus = Field(default=TemplateStatus.DRAFT)


class EmailTemplateRender(BaseModel):
    """The result of rendering an email template with variables."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    template_id: str
    variables: dict[str, str] = Field(default_factory=dict)
    subject_result: str
    body_result: str
    rendered_at: datetime = Field(default_factory=utc_now)


class DesignerConfig(BaseModel):
    """Configuration for the email template designer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_templates: int = Field(default=500, ge=1)
    default_category: str = Field(default="general")
    allow_html: bool = Field(default=True)


__all__ = [
    "DesignerConfig",
    "EmailTemplate",
    "EmailTemplateRender",
    "TemplateStatus",
]
