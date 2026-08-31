"""Configuration management domain models — entries, profiles, changes, validations, snapshots, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ConfigEntryType(StrEnum):
    STRING = "string"
    INTEGER = "int"
    BOOLEAN = "bool"
    FLOAT = "float"
    JSON = "json"
    YAML = "yaml"


class ConfigEntrySource(StrEnum):
    FILE = "file"
    ENV = "env"
    DB = "db"
    API = "api"
    MANUAL = "manual"


class ConfigEntryStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ConfigEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    key: str
    value: str
    type: ConfigEntryType = ConfigEntryType.STRING
    description: str = ""
    tags: tuple[str, ...] = Field(default=())
    source: ConfigEntrySource = ConfigEntrySource.MANUAL
    version: int = 1
    status: ConfigEntryStatus = ConfigEntryStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfigProfileStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ConfigProfile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    environment: str = ""
    entries: dict[str, str] = Field(default_factory=dict)
    parent_profile: str | None = None
    status: ConfigProfileStatus = ConfigProfileStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfigChange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    entry_id: str
    old_value: str = ""
    new_value: str = ""
    changed_by: str = ""
    reason: str = ""
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfigValidation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    entry_id: str
    valid: bool = True
    errors: tuple[str, ...] = Field(default=())
    warnings: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfigSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    profile_id: str
    entries: dict[str, str] = Field(default_factory=dict)
    checksum: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConfigMgtConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enable_audit_logging: bool = True
    enable_versioning: bool = True
    cache_ttl_seconds: int = 300
    max_snapshots: int = 50
    enable_hot_reload: bool = True
    validation_on_update: bool = True


__all__ = [
    "ConfigChange",
    "ConfigEntry",
    "ConfigEntrySource",
    "ConfigEntryStatus",
    "ConfigEntryType",
    "ConfigMgtConfig",
    "ConfigProfile",
    "ConfigProfileStatus",
    "ConfigSnapshot",
    "ConfigValidation",
]
