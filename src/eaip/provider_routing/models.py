"""Data models for provider routing — routes, endpoints, health, load balancing, and failover."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class RouteStatus(StrEnum):
    """Status of a provider route."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    FAILED = "failed"
    DRAINING = "draining"


class RoutingStrategy(StrEnum):
    """Strategy used to select a provider route."""

    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_LOADED = "least_loaded"
    PRIORITY = "priority"
    HEALTH_FIRST = "health_first"
    RANDOM = "random"
    CUSTOM = "custom"


class RouteWeight(BaseModel):
    """Weight assigned to a route for weighted routing strategies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    route_id: str = Field(description="Identifier of the route.")
    weight: int = Field(ge=0, description="Relative weight (higher = more traffic).")
    label: str = Field(default="", description="Optional label for this weight entry.")


class EndpointHealth(BaseModel):
    """Health snapshot of a provider endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    endpoint_id: str = Field(description="Endpoint identifier.")
    healthy: bool = Field(description="Whether the endpoint is currently healthy.")
    last_checked: datetime = Field(
        default_factory=utc_now, description="Last health check timestamp."
    )
    latency_ms: float = Field(default=0.0, description="Last measured latency in milliseconds.")
    error_count: int = Field(default=0, ge=0, description="Consecutive error count.")
    details: dict[str, Any] = Field(default_factory=dict, description="Arbitrary health details.")


class ProviderEndpoint(BaseModel):
    """A provider endpoint that can receive routed requests."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    endpoint_id: str = Field(description="Unique endpoint identifier.")
    provider_id: str = Field(description="Provider this endpoint belongs to.")
    url: str = Field(description="Base URL of the endpoint.")
    weight: int = Field(default=1, ge=0, description="Routing weight.")
    priority: int = Field(default=0, ge=0, description="Priority (lower = preferred).")
    max_concurrent: int = Field(default=10, ge=1, description="Max concurrent requests.")
    tags: tuple[str, ...] = Field(default=(), description="Tags for match criteria.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata.")
    health: EndpointHealth | None = Field(default=None, description="Current health snapshot.")


class HealthCheckConfig(BaseModel):
    """Configuration for endpoint health checking."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, description="Whether health checking is enabled.")
    interval_seconds: float = Field(default=30.0, gt=0, description="Check interval.")
    timeout_seconds: float = Field(default=5.0, gt=0, description="Request timeout.")
    unhealthy_threshold: int = Field(
        default=3,
        ge=1,
        description="Consecutive failures before marking unhealthy.",
    )
    healthy_threshold: int = Field(
        default=2,
        ge=1,
        description="Consecutive successes before marking healthy.",
    )
    endpoint: str = Field(default="/health", description="Health check endpoint path.")


class LoadBalancerConfig(BaseModel):
    """Configuration for load balancing across endpoints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: RoutingStrategy = Field(
        default=RoutingStrategy.ROUND_ROBIN, description="Load-balancing strategy."
    )
    sticky_sessions: bool = Field(
        default=False, description="Whether to pin sessions to the same endpoint."
    )
    max_retries: int = Field(default=3, ge=0, description="Max retries on failure.")
    retry_backoff_ms: float = Field(default=100.0, ge=0, description="Backoff between retries.")
    endpoints: tuple[ProviderEndpoint, ...] = Field(default=(), description="Managed endpoints.")


class FailoverConfig(BaseModel):
    """Configuration for failover behaviour."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, description="Whether failover is enabled.")
    max_attempts: int = Field(default=3, ge=1, description="Max failover attempts.")
    fallback_endpoint_id: str | None = Field(
        default=None, description="Ultimate fallback endpoint."
    )
    circuit_breaker_threshold: int = Field(
        default=5, ge=1, description="Failures before circuit opens."
    )
    circuit_breaker_reset_seconds: float = Field(
        default=60.0,
        gt=0,
        description="Time before circuit resets.",
    )


class RouteMatchCriteria(BaseModel):
    """Criteria used to match a route to a request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str | None = Field(default=None, description="Model name to match.")
    provider_id: str | None = Field(default=None, description="Provider to match.")
    tags: tuple[str, ...] = Field(default=(), description="Tags the route must satisfy.")
    weight_range: tuple[int, int] = Field(
        default=(0, 100), description="Allowed weight range (min, max)."
    )
    custom_matcher: str | None = Field(
        default=None, description="Name of a registered custom matcher."
    )


class RoutingRule(BaseModel):
    """A single routing rule matching requests to routes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str = Field(description="Unique rule identifier.")
    name: str = Field(default="", description="Human-readable name.")
    description: str = Field(default="", description="Rule description.")
    priority: int = Field(
        default=0, ge=0, description="Evaluation priority (lower = evaluated first)."
    )
    match_criteria: RouteMatchCriteria = Field(description="Criteria to match against.")
    target_route_ids: tuple[str, ...] = Field(description="Route(s) to route to when matched.")
    enabled: bool = Field(default=True, description="Whether the rule is active.")


class ProviderRouteConfig(BaseModel):
    """Configuration for a provider route."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: RoutingStrategy = Field(
        default=RoutingStrategy.ROUND_ROBIN, description="Routing strategy."
    )
    load_balancer: LoadBalancerConfig = Field(
        default_factory=LoadBalancerConfig, description="Load-balancer config."
    )
    failover: FailoverConfig = Field(default_factory=FailoverConfig, description="Failover config.")
    health_check: HealthCheckConfig = Field(
        default_factory=HealthCheckConfig, description="Health-check config."
    )
    rules: tuple[RoutingRule, ...] = Field(default=(), description="Ordered routing rules.")
    weights: tuple[RouteWeight, ...] = Field(default=(), description="Per-route weights.")


class ProviderRoute(BaseModel):
    """A provider route — the core routing entity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    route_id: str = Field(description="Unique route identifier.")
    name: str = Field(default="", description="Human-readable name.")
    status: RouteStatus = Field(default=RouteStatus.ACTIVE, description="Current route status.")
    config: ProviderRouteConfig = Field(description="Route configuration.")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp.")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp.")
    tags: tuple[str, ...] = Field(default=(), description="Tags for categorisation.")


class RouteMetrics(BaseModel):
    """Metrics collected for a route."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    route_id: str = Field(description="Route identifier.")
    total_requests: int = Field(default=0, ge=0, description="Total requests routed.")
    successful_requests: int = Field(default=0, ge=0, description="Successful requests.")
    failed_requests: int = Field(default=0, ge=0, description="Failed requests.")
    total_latency_ms: float = Field(default=0.0, ge=0, description="Cumulative latency.")
    average_latency_ms: float = Field(default=0.0, ge=0, description="Average latency.")
    last_request_at: datetime | None = Field(default=None, description="Timestamp of last request.")
    circuit_broken: bool = Field(default=False, description="Whether circuit breaker is open.")


class ProviderRouteAssignment(BaseModel):
    """A request-to-route assignment result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(description="Request identifier.")
    route_id: str = Field(description="Assigned route identifier.")
    endpoint_id: str = Field(description="Assigned endpoint identifier.")
    strategy: RoutingStrategy = Field(description="Strategy used for assignment.")
    assigned_at: datetime = Field(default_factory=utc_now, description="Assignment timestamp.")


class RouteAuditEntry(BaseModel):
    """An audit log entry for route changes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entry_id: str = Field(description="Unique entry identifier.")
    route_id: str = Field(description="Route identifier.")
    action: str = Field(description="Action performed (e.g. created, updated, deleted).")
    actor: str = Field(default="system", description="Actor that performed the action.")
    details: dict[str, Any] = Field(default_factory=dict, description="Action details.")
    timestamp: datetime = Field(default_factory=utc_now, description="Entry timestamp.")


__all__ = [
    "EndpointHealth",
    "FailoverConfig",
    "HealthCheckConfig",
    "LoadBalancerConfig",
    "ProviderEndpoint",
    "ProviderRoute",
    "ProviderRouteAssignment",
    "ProviderRouteConfig",
    "RouteAuditEntry",
    "RouteMatchCriteria",
    "RouteMetrics",
    "RouteStatus",
    "RouteWeight",
    "RoutingRule",
    "RoutingStrategy",
]
