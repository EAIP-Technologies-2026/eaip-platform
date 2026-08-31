"""Data models for the agent skill registry."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SkillCategory(StrEnum):
    NLP = "nlp"
    VISION = "vision"
    CODE = "code"
    DATA = "data"
    TOOL = "tool"
    CUSTOM = "custom"


class SkillRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    version_spec: str = Field(default="*")


class SkillDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    category: SkillCategory
    description: str = Field(default="")
    version: str = Field(default="1.0.0")
    tags: tuple[str, ...] = Field(default=())
    requirements: tuple[SkillRequirement, ...] = Field(default=())
    deprecated: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillMatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    skill_id: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SkillRegistryConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_results: int = Field(default=20, ge=1)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


__all__ = [
    "SkillCategory",
    "SkillDefinition",
    "SkillMatch",
    "SkillRegistryConfig",
    "SkillRequirement",
]
