"""Data models for the model registry — versions, artifacts, entries, and config."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ModelVersion(BaseModel):
    """A single version of a registered model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str
    description: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelArtifact(BaseModel):
    """An artifact associated with a model version."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    uri: str
    type: str
    size_bytes: int = Field(default=0, ge=0)
    checksum: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelRegistryEntry(BaseModel):
    """An entry in the model registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    provider: str
    versions: tuple[ModelVersion, ...] = Field(default=())
    artifacts: tuple[ModelArtifact, ...] = Field(default=())
    is_deprecated: bool = Field(default=False)
    is_archived: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelRegistryConfig(BaseModel):
    """Configuration for the model registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_versions_per_model: int = Field(default=10, ge=1)
    allow_downgrade: bool = Field(default=False)
    auto_archive_old_versions: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300, ge=0)


__all__ = [
    "ModelArtifact",
    "ModelRegistryConfig",
    "ModelRegistryEntry",
    "ModelVersion",
]
