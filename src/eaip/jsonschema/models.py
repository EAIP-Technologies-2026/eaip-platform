"""JSON Schema models — documents, validation results, and configuration."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SchemaStatus(StrEnum):
    ACTIVE = "active"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class SchemaDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    schema_definition: dict[str, object] = Field(default_factory=dict)
    description: str = ""
    version: int = 1
    status: SchemaStatus = SchemaStatus.DRAFT
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SchemaValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    schema_id: str
    document_ref: str = ""
    valid: bool = True
    errors: tuple[str, ...] = Field(default_factory=tuple)
    validated_at: datetime = Field(default_factory=utc_now)


class SchemaConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_schema_size_bytes: int = Field(default=1048576, ge=1)
    enable_draft_validation: bool = Field(default=True)
    require_description: bool = Field(default=False)
    max_validation_errors: int = Field(default=100, ge=1)


__all__ = [
    "SchemaConfig",
    "SchemaDocument",
    "SchemaStatus",
    "SchemaValidationResult",
]
