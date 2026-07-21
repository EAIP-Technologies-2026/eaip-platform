"""Pydantic models for the knowledge curation service."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ContentStatus(StrEnum):
    """Status of a content submission."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class ContentSubmission(BaseModel):
    """A piece of content submitted for curation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for this submission")
    source: str = Field(description="Source of the content")
    content: str = Field(description="The content body")
    content_type: str = Field(
        default="text", description="Type of content (e.g. text, document, code)"
    )
    status: ContentStatus = Field(
        default=ContentStatus.PENDING, description="Current curation status"
    )
    submitted_by: str = Field(description="Who submitted the content")
    submitted_at: datetime = Field(
        default_factory=utc_now, description="When the content was submitted"
    )


class QualityScore(BaseModel):
    """Quality assessment score for submitted content."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    submission_id: str = Field(description="ID of the assessed submission")
    overall_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall quality score (0.0-1.0)"
    )
    relevance: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score (0.0-1.0)")
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Accuracy score (0.0-1.0)")
    completeness: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Completeness score (0.0-1.0)"
    )
    scored_by: str = Field(description="Who or what performed the scoring")
    scored_at: datetime = Field(
        default_factory=utc_now, description="When the scoring was performed"
    )


class CurationReview(BaseModel):
    """A review record for a content submission."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique identifier for this review")
    submission_id: str = Field(description="ID of the reviewed submission")
    reviewer: str = Field(description="Who performed the review")
    decision: ContentStatus = Field(description="Decision made (approved/rejected/flagged)")
    comments: str = Field(default="", description="Reviewer comments")
    score: QualityScore | None = Field(
        default=None, description="Quality score assigned during review"
    )
    reviewed_at: datetime = Field(
        default_factory=utc_now, description="When the review was performed"
    )


class CurationConfig(BaseModel):
    """Configuration for the knowledge curation service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    auto_approve_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Auto-approve quality threshold"
    )
    require_review: bool = Field(default=True, description="Whether human review is required")
    max_pending_per_source: int = Field(
        default=50, ge=1, description="Maximum pending submissions per source"
    )
    history_retention_days: int = Field(
        default=90, ge=1, description="Days to retain submission history"
    )


__all__ = [
    "ContentStatus",
    "ContentSubmission",
    "CurationConfig",
    "CurationReview",
    "QualityScore",
]
