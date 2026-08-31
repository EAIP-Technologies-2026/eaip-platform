"""Data models for Decision Intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DecisionLog(BaseModel):
    """A log entry for a decision made by the system."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    tenant_id: str
    decision_type: str
    context: dict[str, Any] = Field(default_factory=dict)
    outcome: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


__all__ = ["DecisionLog"]
