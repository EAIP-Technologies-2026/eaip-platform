"""Data models for HTTP request router — routes, matches, and config."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RouteStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Route(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    path: str
    method: str = Field(default="GET")
    target_url: str
    middleware: tuple[str, ...] = Field(default=())
    timeout_ms: int = Field(default=5000, ge=1)
    retry_policy: str = Field(default="none")
    status: RouteStatus = Field(default=RouteStatus.ACTIVE)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RouteMatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    route_id: str
    request_path: str
    match_result: dict[str, object] = Field(default_factory=dict)
    priority: int = Field(default=0)
    matched_at: datetime = Field(default_factory=utc_now)


class RouterConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_timeout_ms: int = Field(default=5000, ge=1)
    max_routes: int = Field(default=1000, ge=1)
    allow_method_override: bool = Field(default=False)
    retry_default: str = Field(default="none")


__all__ = [
    "Route",
    "RouteMatch",
    "RouteStatus",
    "RouterConfig",
]
