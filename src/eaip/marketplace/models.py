"""Marketplace domain models — packages, versions, installations."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class PackageType(StrEnum):
    AGENT = "agent"
    TOOL = "tool"
    PLUGIN = "plugin"
    TEMPLATE = "template"
    ADAPTER = "adapter"


class PackageStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class MarketplacePackage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    package_id: str
    name: str
    type: PackageType
    version: str
    description: str
    author: str
    dependencies: tuple[str, ...] = Field(default=())
    tags: tuple[str, ...] = Field(default=())
    status: PackageStatus = Field(default=PackageStatus.DRAFT)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    downloads: int = Field(default=0)
    rating: float = Field(default=0.0)
    metadata: dict[str, str] = Field(default_factory=dict)


class PackageVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    package_id: str
    version: str
    semver_range: str
    changelog: str
    created_at: datetime = Field(default_factory=utc_now)
    checksum: str
    size_bytes: int
    is_compatible: bool = Field(default=True)


class PackageInstallation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    installation_id: str
    package_id: str
    version: str
    installed_at: datetime = Field(default_factory=utc_now)
    installed_by: str
    status: str
    metadata: dict[str, str] = Field(default_factory=dict)
