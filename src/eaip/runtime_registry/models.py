from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RuntimeKind(StrEnum):
    local_runtime = "local_runtime"
    worker_runtime = "worker_runtime"
    isolated_runtime = "isolated_runtime"
    remote_runtime = "remote_runtime"


class RuntimeStatus(StrEnum):
    healthy = "healthy"
    degraded = "degraded"
    offline = "offline"


class RuntimeRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    runtime_id: str
    kind: RuntimeKind = RuntimeKind.local_runtime
    name: str
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    status: RuntimeStatus = RuntimeStatus.healthy
    tenant_id: str = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
