"""Ops Intelligence models — Insight."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class Insight(BaseModel):
    """Operational insight produced by detector/service.

    Frozen: insights are immutable once created.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    insight_id: str
    tenant_id: str
    type: str = Field(description="anomaly | bottleneck | risk | opportunity")
    severity: str = Field(description="low | medium | high | critical")
    evidence: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    source: str = Field(default="detector", description="detector | manual | system")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    affected_systems: tuple[str, ...] = Field(default_factory=tuple)
    recommendation: str = Field(default="")
    status: str = Field(default="open", description="open | acknowledged | escalated | closed")
    created_at: datetime = Field(default_factory=utc_now)


__all__ = ["Insight"]
