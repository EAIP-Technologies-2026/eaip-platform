"""Data models for image tag management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ImageTag(BaseModel):
    """A tag pointing to a container image digest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    repository: str
    digest: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ImageManifest(BaseModel):
    """A container image manifest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    repository: str
    tags: tuple[str, ...] = Field(default=())
    digest: str
    size_bytes: int = Field(default=0, ge=0)
    layers: int = Field(default=0, ge=0)
    os: str = Field(default="linux")
    architecture: str = Field(default="amd64")
    pushed_at: datetime = Field(default_factory=utc_now)


class TagConfig(BaseModel):
    """Configuration for the image tag manager."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_tags_per_repository: int = Field(default=100, ge=1)
    allow_overwrite: bool = Field(default=False)
    enforce_digest_validation: bool = Field(default=True)


__all__ = [
    "ImageManifest",
    "ImageTag",
    "TagConfig",
]
