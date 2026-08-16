"""Data models for Intelligence Pulse."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PulseMetric(BaseModel):
    """A single metric recorded by the Intelligence Pulse."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    name: str
    value: float
    dimensions: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


__all__ = ["PulseMetric"]
