"""Data models for agent templates — blueprints, categories, parameters, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class TemplateCategory(StrEnum):
    """Enumeration of agent template categories."""

    CHAT = "chat"
    TASK = "task"
    WORKFLOW = "workflow"
    ANALYST = "analyst"
    CUSTOM = "custom"


class TemplateParameter(BaseModel):
    """A parameter definition for an agent template."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: str
    description: str = Field(default="")
    required: bool = Field(default=False)
    default_value: Any = Field(default=None)


class AgentTemplate(BaseModel):
    """A predefined agent blueprint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    category: TemplateCategory
    version: str = Field(default="1.0.0")
    parameters: tuple[TemplateParameter, ...] = Field(default=())
    is_deprecated: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TemplateConfig(BaseModel):
    """Configuration for the agent template engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_templates: int = Field(default=100, ge=1)
    allow_custom_templates: bool = Field(default=True)
    default_category: TemplateCategory = Field(default=TemplateCategory.CUSTOM)
    cache_ttl_seconds: int = Field(default=300, ge=0)


__all__ = [
    "AgentTemplate",
    "TemplateCategory",
    "TemplateConfig",
    "TemplateParameter",
]
