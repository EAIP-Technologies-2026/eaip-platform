"""Data masking domain models — rules, jobs, detection, classification, config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MaskingStrategy(StrEnum):
    MASK = "mask"
    TRUNCATE = "truncate"
    HASH = "hash"
    REDACT = "redact"
    ENCRYPT = "encrypt"
    SUBSTITUTE = "substitute"


class DataType(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "creditcard"
    NAME = "name"
    ADDRESS = "address"
    IP = "ip"
    CUSTOM = "custom"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ClassificationLevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    CRITICAL = "critical"


class MaskingRule(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    field_pattern: str
    data_type: DataType
    strategy: MaskingStrategy
    mask_character: str = Field(default="*")
    preserve_length: bool = Field(default=True)
    preserve_prefix_count: int = Field(default=0)
    substitution_dict: dict[str, str] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnonymizationJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    source: str
    rules: tuple[MaskingRule, ...] = Field(default=())
    status: JobStatus = Field(default=JobStatus.PENDING)
    records_processed: int = Field(default=0)
    records_skipped: int = Field(default=0)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PiiDetectionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    field_name: str
    detected_types: tuple[str, ...] = Field(default=())
    confidence: float = Field(default=0.0)
    occurrence_count: int = Field(default=0)
    sample_values: tuple[str, ...] = Field(default=())
    location: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataClassificationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    data_type: str
    classification_level: ClassificationLevel
    findings: tuple[str, ...] = Field(default=())
    score: float = Field(default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MaskingConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_mask_char: str = Field(default="*")
    enable_pii_detection: bool = Field(default=True)
    enable_audit_logging: bool = Field(default=True)
    max_parallel_jobs: int = Field(default=4)
    field_discovery_enabled: bool = Field(default=True)
