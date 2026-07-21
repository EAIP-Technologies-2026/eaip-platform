"""Data models for the enterprise template engine."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TemplateFormat(StrEnum):
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"


class TemplateVariable(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: str = Field(default="string")
    required: bool = Field(default=False)
    default: str | None = Field(default=None)


class TemplateDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    content: str
    format: TemplateFormat = Field(default=TemplateFormat.TEXT)
    variables: tuple[TemplateVariable, ...] = Field(default=())
    description: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    content: str
    format: TemplateFormat
    variables_used: tuple[str, ...] = Field(default=())


class TemplateEngineConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_template_size: int = Field(default=1048576, ge=1)
    cache_enabled: bool = Field(default=True)


__all__ = [
    "RenderResult",
    "TemplateDefinition",
    "TemplateEngineConfig",
    "TemplateFormat",
    "TemplateVariable",
]
