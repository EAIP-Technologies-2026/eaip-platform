"""Domain events for HTTP request router."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from eaip.events.event import DomainEvent


class RouteRegistered(DomainEvent):
    event_type: ClassVar[str] = "eaip.httprouter.route.registered"

    route_id: str
    path: str
    method: str
    target_url: str


class RouteUpdated(DomainEvent):
    event_type: ClassVar[str] = "eaip.httprouter.route.updated"

    route_id: str
    changes: dict[str, Any] = Field(default_factory=dict)


class RouteDeactivated(DomainEvent):
    event_type: ClassVar[str] = "eaip.httprouter.route.deactivated"

    route_id: str
    reason: str = Field(default="")


class RequestRouted(DomainEvent):
    event_type: ClassVar[str] = "eaip.httprouter.request.routed"

    route_id: str
    request_path: str
    method: str
    target_url: str


__all__ = [
    "RequestRouted",
    "RouteDeactivated",
    "RouteRegistered",
    "RouteUpdated",
]
