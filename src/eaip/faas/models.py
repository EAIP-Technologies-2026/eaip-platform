"""Data models for Function as a Service runtime."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FunctionRuntime(StrEnum):
    PYTHON = "python"
    NODEJS = "nodejs"
    GO = "go"
    RUST = "rust"


class FunctionStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Function(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    runtime: FunctionRuntime
    handler: str
    code_ref: str
    timeout_seconds: int = Field(default=30, ge=1)
    memory_mb: int = Field(default=128, ge=1)
    status: FunctionStatus = Field(default=FunctionStatus.ACTIVE)


class FunctionExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    function_id: str
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: int | None = Field(default=None)
    output: str = Field(default="")
    error: str = Field(default="")


class FaaSConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_timeout_seconds: int = Field(default=30, ge=1)
    default_memory_mb: int = Field(default=128, ge=1)
    max_concurrent_executions: int = Field(default=100, ge=1)
    enable_auto_scaling: bool = Field(default=True)
    min_instances: int = Field(default=0, ge=0)
    max_instances: int = Field(default=10, ge=1)


__all__ = [
    "ExecutionStatus",
    "FaaSConfig",
    "Function",
    "FunctionExecution",
    "FunctionRuntime",
    "FunctionStatus",
]
