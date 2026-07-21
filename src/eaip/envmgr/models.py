"""Data models for environment variable management — variables, groups, and config."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class EnvironmentVariable(BaseModel):
    """A single environment variable with versioning and metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    value: str
    environment: str = Field(default="default")
    scope: str = Field(default="application")
    is_secret: bool = Field(default=False)
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    description: str = Field(default="")


class VariableGroup(BaseModel):
    """A named group of environment variables."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    variables: tuple[str, ...] = Field(default=())
    environment: str = Field(default="default")
    created_at: datetime = Field(default_factory=utc_now)


class EnvMgrConfig(BaseModel):
    """Configuration for the environment variable manager."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True)
    max_variable_value_length: int = Field(default=8192, ge=1)
    allow_secrets: bool = Field(default=True)
    version_history_limit: int = Field(default=10, ge=1)
    validate_names: bool = Field(default=True)


__all__ = [
    "EnvMgrConfig",
    "EnvironmentVariable",
    "VariableGroup",
]
