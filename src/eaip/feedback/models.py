"""Data models for feedback collection — items, ratings, categories, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class FeedbackRating(StrEnum):
    """Enumeration of possible feedback ratings."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FeedbackCategory(StrEnum):
    """Enumeration of feedback categories."""

    BUG = "bug"
    FEATURE = "feature"
    PERFORMANCE = "performance"
    UX = "ux"
    OTHER = "other"


class FeedbackItem(BaseModel):
    """A single feedback submission."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    user_id: str
    rating: FeedbackRating
    category: FeedbackCategory
    message: str = Field(default="")
    source: str = Field(default="")
    acknowledged: bool = Field(default=False)
    escalated: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackConfig(BaseModel):
    """Configuration for the feedback collection engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_message_length: int = Field(default=2000, ge=1)
    require_category: bool = Field(default=True)
    auto_escalate_threshold: int = Field(default=10, ge=0)


__all__ = [
    "FeedbackCategory",
    "FeedbackConfig",
    "FeedbackItem",
    "FeedbackRating",
]
