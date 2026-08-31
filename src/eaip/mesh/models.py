"""Data models for the EAIP service mesh."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class ServiceStatus(StrEnum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


class RoutingStrategy(StrEnum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED = "weighted"
    HEALTH_BASED = "health_based"


class ServiceInstance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique instance identifier.")
    name: str = Field(description="Service name.")
    version: str = Field(default="1.0.0", description="Service version.")
    host: str = Field(description="Host address.")
    port: int = Field(gt=0, le=65535, description="Service port.")
    protocol: str = Field(default="http", description="Communication protocol.")
    status: ServiceStatus = Field(
        default=ServiceStatus.UNKNOWN, description="Current health status."
    )
    health_endpoint: str = Field(default="", description="Health check endpoint path.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata.")
    tags: tuple[str, ...] = Field(default=(), description="Categorisation tags.")
    registered_at: datetime = Field(default_factory=utc_now, description="Registration timestamp.")
    last_heartbeat: datetime = Field(
        default_factory=utc_now, description="Last heartbeat timestamp."
    )
    weight: int = Field(default=1, ge=1, description="Routing weight.")


class ServiceRoute(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique route identifier.")
    name: str = Field(description="Human-readable route name.")
    source_service: str = Field(description="Source service name.")
    destination_service: str = Field(description="Destination service name.")
    routing_strategy: RoutingStrategy = Field(
        default=RoutingStrategy.ROUND_ROBIN, description="Routing strategy."
    )
    conditions: tuple[str, ...] = Field(default=(), description="Routing condition expressions.")
    fallback_service: str = Field(default="", description="Fallback service name.")
    timeout_seconds: float = Field(default=30.0, gt=0, description="Request timeout.")
    retry_count: int = Field(default=3, ge=0, description="Max retries.")
    circuit_breaker_config: dict[str, Any] = Field(
        default_factory=dict, description="Circuit breaker configuration."
    )
    enabled: bool = Field(default=True, description="Whether the route is active.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata.")


class LoadBalancerState(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    service_name: str = Field(description="Service name this state tracks.")
    current_index: int = Field(default=0, ge=0, description="Current round-robin index.")
    active_connections: dict[str, int] = Field(
        default_factory=dict, description="Instance ID to active connection count."
    )
    strategy: RoutingStrategy = Field(
        default=RoutingStrategy.ROUND_ROBIN, description="Current strategy."
    )
    last_distribution: str | None = Field(default=None, description="Last selected instance ID.")


class MeshConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    heartbeat_interval_seconds: float = Field(
        default=15.0, gt=0, description="Interval between heartbeats."
    )
    health_check_timeout: float = Field(default=5.0, gt=0, description="Health check timeout.")
    circuit_breaker_threshold: int = Field(
        default=5, gt=0, description="Failure threshold before opening circuit."
    )
    max_retries: int = Field(default=3, ge=0, description="Default max retries for mesh calls.")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing.")
    metrics_port: int = Field(default=9090, ge=1024, le=65535, description="Metrics export port.")


__all__ = [
    "LoadBalancerState",
    "MeshConfig",
    "RoutingStrategy",
    "ServiceInstance",
    "ServiceRoute",
    "ServiceStatus",
]
