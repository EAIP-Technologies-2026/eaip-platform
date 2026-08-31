"""Data models for host discovery — hosts, jobs, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class HostStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class JobStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Host(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    hostname: str
    ip_address: str
    os: str = Field(default="")
    platform: str = Field(default="")
    agent_version: str = Field(default="")
    tags: tuple[str, ...] = Field(default=())
    status: HostStatus = Field(default=HostStatus.UNKNOWN)
    last_seen: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)


class DiscoveryJob(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    cidr_range: str
    ports: tuple[int, ...] = Field(default=())
    completed_hosts: int = Field(default=0)
    total_hosts: int = Field(default=0)
    status: JobStatus = Field(default=JobStatus.RUNNING)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)


class DiscoveryConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_cidr: str = Field(default="10.0.0.0/24")
    default_ports: tuple[int, ...] = Field(default=(22, 80, 443))
    scan_timeout_seconds: int = Field(default=30, ge=1)
    max_concurrent_scans: int = Field(default=10, ge=1)


__all__ = [
    "DiscoveryConfig",
    "DiscoveryJob",
    "Host",
    "HostStatus",
    "JobStatus",
]
