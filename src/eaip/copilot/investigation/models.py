"""Investigation domain models — state machine, evidence, timeline, context.

An investigation is a persistent, bounded, auditable analytical session.
It reuses existing EAIP tools, governance, and memory infrastructure.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class InvestigationStatus(StrEnum):
    """Bounded lifecycle states for an investigation."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    WAITING = "waiting"
    RESOLVED = "resolved"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"


class EvidenceType(StrEnum):
    """Provenance classification for investigation evidence."""

    OBSERVED = "observed"
    INFERRED = "inferred"
    RECOMMENDED = "recommended"


class EvidenceSource(StrEnum):
    """Where the evidence came from."""

    TOOL = "tool"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    EVENT = "event"
    USER = "user"
    SYSTEM = "system"


class InvestigationPriority(StrEnum):
    """Investigation urgency level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Evidence(BaseModel):
    """A single piece of evidence with provenance classification.

    Evidence MUST distinguish OBSERVED (verified fact), INFERRED (reasoning),
    and RECOMMENDED (suggested action).  These classifications must NEVER be
    silently promoted: INFERRED -> OBSERVED or RECOMMENDED -> EXECUTED.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    investigation_id: str
    evidence_type: EvidenceType
    source: EvidenceSource
    content: str
    source_tool: str = ""
    source_route: str = ""
    confidence: float = 1.0
    timestamp: datetime = Field(default_factory=utc_now)
    stale: bool = False
    stale_reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""


class TimelineEvent(BaseModel):
    """An auditable event in an investigation's timeline."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    investigation_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    event_type: str
    description: str
    actor_id: str = "system"
    evidence_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Hypothesis(BaseModel):
    """A working hypothesis generated during an investigation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    investigation_id: str
    statement: str
    confidence: float = 0.5
    supporting_evidence_ids: tuple[str, ...] = ()
    contradicting_evidence_ids: tuple[str, ...] = ()
    status: str = "active"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Investigation(BaseModel):
    """A persistent investigation into an enterprise operational question.

    An investigation is owned by a user within a tenant.  It tracks evidence,
    hypotheses, findings, and recommendations with full provenance.  It does
    NOT grant authorization — all tool access goes through normal governance.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    tenant_id: str
    owner_id: str
    title: str
    objective: str
    status: InvestigationStatus = InvestigationStatus.DRAFT
    priority: InvestigationPriority = InvestigationPriority.MEDIUM
    current_stage: str = "evidence_gathering"
    summary: str = ""
    findings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    related_entities: tuple[str, ...] = ()
    related_routes: tuple[str, ...] = ()
    related_events: tuple[str, ...] = ()
    memory_references: tuple[str, ...] = ()
    correlation_ids: tuple[str, ...] = ()
    max_reasoning_steps: int = 20
    reasoning_steps_used: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_activity_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    expires_at: datetime | None = None
    retention_policy: str = "30d"
    provenance: str = "conductor_investigation"


class CreateInvestigationRequest(BaseModel):
    """Request to create a new investigation."""

    model_config = ConfigDict(extra="ignore")

    title: str
    objective: str
    priority: InvestigationPriority = InvestigationPriority.MEDIUM
    related_entities: tuple[str, ...] = ()
    related_routes: tuple[str, ...] = ()


class InvestigationCommand(BaseModel):
    """Command to send to an active investigation."""

    model_config = ConfigDict(extra="ignore")

    command: str = "continue"
    context: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "CreateInvestigationRequest",
    "Evidence",
    "EvidenceSource",
    "EvidenceType",
    "Hypothesis",
    "Investigation",
    "InvestigationCommand",
    "InvestigationPriority",
    "InvestigationStatus",
    "TimelineEvent",
]
