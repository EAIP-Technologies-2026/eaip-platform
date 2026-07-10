"""Domain events emitted by the gateway."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class EndpointRegistered(DomainEvent):
    """Published when an endpoint is registered with the router."""

    event_type: ClassVar[str] = "eaip.gateway.endpoint.registered"

    path: str
    method: str


class EndpointUnregistered(DomainEvent):
    """Published when an endpoint is removed from the router."""

    event_type: ClassVar[str] = "eaip.gateway.endpoint.unregistered"

    path: str
    method: str


class ApiRequestProcessed(DomainEvent):
    """Published after an API request is fully processed."""

    event_type: ClassVar[str] = "eaip.gateway.request.processed"

    request_id: str
    path: str
    method: str
    status_code: int
    duration_ms: float


__all__ = [
    "ApiRequestProcessed",
    "EndpointRegistered",
    "EndpointUnregistered",
]
