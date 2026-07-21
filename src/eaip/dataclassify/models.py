"""Data classification domain models — classes, results, config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DataCategory(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DataClass(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    pattern: str = Field(default="")
    category: DataCategory
    priority: int = Field(default=0)


class ClassificationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    resource_id: str
    detected_classes: tuple[str, ...] = Field(default=())
    confidence: float = Field(default=0.0)
    classified_at: datetime = Field(default_factory=datetime.now)


class ClassifierConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_rules: int = Field(default=100)
    confidence_threshold: float = Field(default=0.7)
    enable_auto_classify: bool = Field(default=True)


__all__ = ["ClassificationResult", "ClassifierConfig", "DataCategory", "DataClass"]
