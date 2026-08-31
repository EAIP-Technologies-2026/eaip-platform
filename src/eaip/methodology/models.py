"""Methodology models — versioned capabilities for reasoning, planning, etc.

All models are frozen Pydantic, tenant-isolated, with UTC timestamps.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from eaip.shared.time import utc_now


class MethodologyCategory(StrEnum):
    reasoning = "reasoning"
    planning = "planning"
    optimization = "optimization"
    forecasting = "forecasting"
    decision = "decision"
    risk = "risk"
    evidence = "evidence"
    simulation = "simulation"
    coordination = "coordination"


class MethodologyRecord(BaseModel):
    """Versioned methodology / capability record.

    Attributes:
        methodology_id: Stable logical id (shared across versions).
        tenant_id: Owning tenant.
        name: Human-readable name.
        version: Semver-like version string.
        category: One of the MethodologyCategory values.
        provider: Provider or author.
        capabilities: Declared capabilities.
        input_requirements: JSON-schema-like input contract.
        output_contract: JSON-schema-like output contract.
        cost: Cost estimate (abstract units).
        latency: Expected latency in ms.
        reliability: Reliability score in [0, 1].
        benchmark_score: Benchmark score (higher is better).
        supported_domains: Domains this methodology applies to.
        lifecycle_status: active / deprecated / retired.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    methodology_id: str
    tenant_id: str
    name: str
    version: str = Field(default="1.0.0")
    category: MethodologyCategory = MethodologyCategory.reasoning
    provider: str = Field(default="eaip")
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    input_requirements: dict[str, Any] = Field(default_factory=dict)
    output_contract: dict[str, Any] = Field(default_factory=dict)
    cost: float = Field(default=0.0, ge=0.0)
    latency: float = Field(default=0.0, ge=0.0)
    reliability: float = Field(default=0.95, ge=0.0, le=1.0)
    benchmark_score: float = Field(default=0.0, ge=0.0)
    supported_domains: tuple[str, ...] = Field(default_factory=tuple)
    lifecycle_status: str = Field(default="active")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("version must be non-empty string")
        return v.strip()

    @field_validator("lifecycle_status")
    @classmethod
    def _validate_lifecycle(cls, v: str) -> str:
        allowed = {"active", "deprecated", "retired", "draft"}
        if v not in allowed:
            return v.lower()
        return v


__all__ = ["MethodologyCategory", "MethodologyRecord"]
