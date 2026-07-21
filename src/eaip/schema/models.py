"""Data models for the schema registry subsystem."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SchemaType(StrEnum):
    AVRO = "avro"
    JSON_SCHEMA = "json_schema"
    PROTOBUF = "protobuf"
    XML = "xml"


class SchemaStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class CompatibilityType(StrEnum):
    BACKWARD = "backward"
    FORWARD = "forward"
    FULL = "full"
    NONE = "none"


class SchemaDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: SchemaType
    version: str
    schema_content: str
    description: str = Field(default="")
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    status: SchemaStatus = Field(default=SchemaStatus.ACTIVE)


class SchemaVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    schema_id: str
    version: str
    content: str
    compatibility: CompatibilityType = Field(default=CompatibilityType.BACKWARD)
    change_log: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    author: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompatibilityResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    schema_id: str
    source_version: str
    target_version: str
    compatible: bool
    violations: tuple[str, ...] = Field(default=())
    check_type: CompatibilityType = Field(default=CompatibilityType.BACKWARD)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SchemaValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    schema_id: str
    valid: bool
    errors: tuple[str, ...] = Field(default=())
    warnings: tuple[str, ...] = Field(default=())
    data_sample: dict[str, Any] | None = Field(default=None)


class SchemaConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_compatibility: CompatibilityType = Field(default=CompatibilityType.BACKWARD)
    enable_validation: bool = Field(default=True)
    enable_evolution: bool = Field(default=True)
    max_versions: int = Field(default=100)
    cache_ttl_seconds: int = Field(default=300)


__all__ = [
    "CompatibilityResult",
    "CompatibilityType",
    "SchemaConfig",
    "SchemaDefinition",
    "SchemaStatus",
    "SchemaType",
    "SchemaValidationResult",
    "SchemaVersion",
]
