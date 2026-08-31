"""Data models for guardrails — rules, results, and configuration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class GuardrailRule(BaseModel):
    """A single guardrail rule definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    pattern: str
    enabled: bool = Field(default=True)
    priority: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GuardrailResult(BaseModel):
    """The result of evaluating a guardrail rule."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str
    passed: bool
    message: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=utc_now)


class GuardrailConfig(BaseModel):
    """Configuration for the guardrails engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_rules: int = Field(default=100, ge=1)
    strict_mode: bool = Field(default=False)
    cache_ttl_seconds: int = Field(default=60, ge=0)


__all__ = [
    "GuardrailConfig",
    "GuardrailResult",
    "GuardrailRule",
]
