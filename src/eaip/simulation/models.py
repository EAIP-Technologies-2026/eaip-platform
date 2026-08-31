"""Simulation domain models — events, scenarios, and enterprise state."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SimulationEvent(BaseModel):
    """A single enterprise simulation event."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    enterprise: str = Field(description="apex | nova | meridian")
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class SimulationScenario(BaseModel):
    """A scenario grouping for an enterprise."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    enterprise: str
    name: str
    description: str = ""
    phases: tuple[str, ...] = Field(default_factory=tuple)


class EnterpriseState(BaseModel):
    """Snapshot of enterprise workload and health."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enterprise: str
    workload: float = Field(ge=0.0, le=1.0)
    utilization: float = Field(ge=0.0, le=1.0)
    active_tasks: int = Field(ge=0)
    alerts: int = Field(ge=0)


__all__ = ["EnterpriseState", "SimulationEvent", "SimulationScenario"]
