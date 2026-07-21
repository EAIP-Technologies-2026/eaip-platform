"""Customer feedback models — items, aggregates, config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class FeedbackItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    customer_id: str
    source: str
    rating: int
    category: str
    sentiment: str | None = None
    comment: str | None = None
    submitted_at: datetime = Field(default_factory=utc_now)
    analyzed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackAggregate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    period: str
    category: str
    avg_rating: float
    count: int
    sentiment_distribution: dict[str, int] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utc_now)


class AnalyzerConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    min_feedback_for_aggregation: int = Field(default=5)
    aggregation_interval_hours: int = Field(default=24)
    enable_sentiment_analysis: bool = Field(default=True)
    data_retention_days: int = Field(default=365)
