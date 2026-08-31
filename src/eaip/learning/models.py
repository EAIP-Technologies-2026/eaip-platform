"""Learning models — LearningRecord, Lesson, AdaptationProposal, enums."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class LearningSource(StrEnum):
    """Source of a learning observation."""

    DECISION = "decision"
    OUTCOME = "outcome"
    FAILURE = "failure"
    SUCCESS = "success"
    MISSION = "mission"
    WORKFLOW = "workflow"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"
    FEEDBACK = "feedback"
    AGENT_PERFORMANCE = "agent_performance"
    WORKFORCE_PERFORMANCE = "workforce_performance"
    STRATEGY_PERFORMANCE = "strategy_performance"


class LearningStatus(StrEnum):
    """Lifecycle status for learning records and lessons."""

    PROPOSED = "proposed"
    VALIDATING = "validating"
    APPROVED = "approved"
    ACTIVATED = "activated"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class RiskLevel(StrEnum):
    """Risk level for adaptation proposals."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AdaptationTarget(StrEnum):
    """Target type for adaptation proposals."""

    WORKFLOW = "workflow"
    METHODOLOGY = "methodology"
    POLICY = "policy"
    AGENT_CONFIG = "agent_config"
    MODEL_ROUTING = "model_routing"
    KNOWLEDGE = "knowledge"


class LearningRecord(BaseModel):
    """A raw observation that may lead to a lesson."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    source_type: LearningSource
    source_id: str
    observation: dict[str, Any] = Field(default_factory=dict)
    evaluation: dict[str, Any] = Field(default_factory=dict)
    proposed_learning: str = ""
    confidence: float = 0.0
    applicability: str = ""
    scope: str = ""
    status: LearningStatus = LearningStatus.PROPOSED
    created_at: datetime = Field(default_factory=utc_now)
    activated_at: datetime | None = None


class Lesson(BaseModel):
    """A validated, approvable lesson derived from learning records."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    learning_record_id: str
    title: str
    description: str = ""
    evidence: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    confidence: float = 0.0
    applicability_scope: str = ""
    status: LearningStatus = LearningStatus.PROPOSED
    approval_id: str = ""
    effective_date: datetime | None = None
    supersedes: str = ""


class AdaptationProposal(BaseModel):
    """A proposed change derived from a lesson."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    lesson_id: str
    target_type: AdaptationTarget
    target_id: str = ""
    proposed_change: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    status: LearningStatus = LearningStatus.PROPOSED
    approval_id: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class FeedbackRecord(BaseModel):
    """A record linking predictions/decisions to actual outcomes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    source_type: LearningSource
    source_id: str
    actual_outcome: dict[str, Any] = Field(default_factory=dict)
    error: float = 0.0
    quality_score: float = 0.0
    created_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "AdaptationProposal",
    "AdaptationTarget",
    "FeedbackRecord",
    "LearningRecord",
    "LearningSource",
    "LearningStatus",
    "Lesson",
    "RiskLevel",
]
