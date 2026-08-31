"""Data models for the sandbox environment manager."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EnvironmentType(StrEnum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    SANDBOX = "sandbox"


class EnvironmentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class SandboxStatus(StrEnum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    EXPIRED = "expired"


class Environment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: EnvironmentType
    status: EnvironmentStatus = Field(default=EnvironmentStatus.ACTIVE)
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class SandboxTemplate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    image: str = Field(default="")
    resources: dict[str, Any] = Field(default_factory=dict)
    startup_script: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class SandboxConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_ttl_minutes: int = Field(default=60, ge=1)
    max_sandboxes_per_environment: int = Field(default=10, ge=1)
    allowed_templates: list[str] = Field(default_factory=list)
    network_policy: dict[str, Any] = Field(default_factory=dict)


class Sandbox(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    environment_id: str
    template_id: str = Field(default="")
    ttl_minutes: int = Field(default=60, ge=1)
    expires_at: datetime = Field(default_factory=lambda: utc_now())
    status: SandboxStatus = Field(default=SandboxStatus.CREATING)
    created_at: datetime = Field(default_factory=utc_now)
    stopped_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "Environment",
    "EnvironmentStatus",
    "EnvironmentType",
    "Sandbox",
    "SandboxConfig",
    "SandboxStatus",
    "SandboxTemplate",
]
