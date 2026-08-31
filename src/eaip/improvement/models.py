"""ImprovementProposal — continuous improvement model."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ImprovementProposal(BaseModel):
    """Continuous improvement proposal (frozen).

    Lifecycle: OUTCOME -> EVALUATE -> PROPOSE -> SIMULATE -> REVIEW -> DEPLOY -> MEASURE
    Status reflects current phase.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    proposal_id: str
    tenant_id: str
    source: str = Field(description="ops_intelligence | manual | system | audit")
    problem: dict[str, Any] = Field(default_factory=dict)
    root_cause: str = Field(default="")
    proposed_change: str = Field(default="")
    expected_benefit: str = Field(default="")
    risk: str = Field(default="low", description="low | medium | high | critical")
    evidence: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    simulation: dict[str, Any] = Field(default_factory=dict)
    approval: dict[str, Any] = Field(default_factory=dict)
    implementation: dict[str, Any] = Field(default_factory=dict)
    measured_outcome: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="proposed", description="proposed | simulated | review | approved | rejected | deployed | measured | closed")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


__all__ = ["ImprovementProposal"]
