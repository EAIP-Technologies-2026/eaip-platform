"""PolicyEvaluationContext — the request context for policy evaluation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now


class PolicyEvaluationContext(BaseModel):
    """The context against which policy rules are evaluated."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str
    subject_roles: tuple[str, ...] = ()
    action: str
    resource: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)
    correlation_id: CorrelationId | None = None


__all__ = ["PolicyEvaluationContext"]
