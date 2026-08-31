"""Declarative Skill models for EAIP Conductor Extensibility (Phase 4)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from eaip.copilot.models import RiskTier


class ConductorSkill(BaseModel):
    """Declarative skill definition composing platform capabilities."""

    id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "OPERATIONS"  # OPERATIONS, DIAGNOSTICS, KNOWLEDGE, WORKFLOW, BRIEFING
    allowed_tools: list[str] = Field(default_factory=list)
    required_permissions: list[str] = Field(default_factory=list)
    risk_level: RiskTier = RiskTier.INFORMATIONAL
    approval_required: bool = False
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class SkillResult(BaseModel):
    """Structured result returned by a skill execution."""

    skill_id: str
    status: str = "success"  # success, pending_approval, error
    summary: str
    observed: str | None = None
    inferred: str | None = None
    recommended: str | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    pending_approval: Any = None
