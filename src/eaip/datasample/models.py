"""Data sampling domain models — definitions, results, config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SamplingStrategy(StrEnum):
    RANDOM = "random"
    STRATIFIED = "stratified"
    SEQUENTIAL = "sequential"


class SampleStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class SampleDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source: str
    strategy: SamplingStrategy
    sample_size: int = Field(default=100)
    sample_percentage: float = Field(default=10.0)
    filters: dict[str, str] = Field(default_factory=dict)
    enabled: bool = Field(default=True)


class SampleResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    definition_id: str
    sampled_records: int = Field(default=0)
    total_records: int = Field(default=0)
    sampled_at: datetime = Field(default_factory=datetime.now)
    status: SampleStatus = Field(default=SampleStatus.PENDING)


class SamplingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_sample_size: int = Field(default=10000)
    default_strategy: SamplingStrategy = Field(default=SamplingStrategy.RANDOM)
    enable_audit_logging: bool = Field(default=True)


__all__ = [
    "SampleDefinition",
    "SampleResult",
    "SampleStatus",
    "SamplingConfig",
    "SamplingStrategy",
]
