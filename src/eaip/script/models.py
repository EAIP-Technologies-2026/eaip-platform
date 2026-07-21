"""Script runtime models — ScriptFunction, ScriptExecution, ScriptConfig."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScriptFunctionStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


class ScriptExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ScriptLanguage(StrEnum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    LUA = "lua"
    RUBY = "ruby"


class ScriptFunction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    language: ScriptLanguage
    source_code: str
    version: str = "1.0.0"
    description: str = ""
    parameters: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    timeout_seconds: float = 30.0
    tags: tuple[str, ...] = Field(default_factory=tuple)
    status: ScriptFunctionStatus = ScriptFunctionStatus.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScriptExecution(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    function_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: str = ""
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    status: ScriptExecutionStatus = ScriptExecutionStatus.PENDING
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScriptConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_execution_time: float = 30.0
    max_memory_mb: int = 128
    allowed_imports: tuple[str, ...] = Field(default_factory=tuple)
    enable_sandbox: bool = True
    max_concurrent_executions: int = 10


__all__ = [
    "ScriptConfig",
    "ScriptExecution",
    "ScriptExecutionStatus",
    "ScriptFunction",
    "ScriptFunctionStatus",
    "ScriptLanguage",
]
