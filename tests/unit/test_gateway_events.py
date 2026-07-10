"""Tests for :mod:`eaip.gateway.events`."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.gateway.events import (
    ApiRequestProcessed,
    EndpointRegistered,
    EndpointUnregistered,
)


class TestEndpointRegistered:
    def test_is_domain_event(self) -> None:
        assert issubclass(EndpointRegistered, DomainEvent)

    def test_fields(self) -> None:
        evt = EndpointRegistered(path="/api/v1/test", method="GET")
        assert evt.path == "/api/v1/test"
        assert evt.method == "GET"
        assert evt.event_type == "eaip.gateway.endpoint.registered"

    def test_frozen(self) -> None:
        evt = EndpointRegistered(path="/test", method="POST")
        with pytest.raises(ValueError):
            evt.path = "/other"


class TestEndpointUnregistered:
    def test_is_domain_event(self) -> None:
        assert issubclass(EndpointUnregistered, DomainEvent)

    def test_fields(self) -> None:
        evt = EndpointUnregistered(path="/api/v1/test", method="DELETE")
        assert evt.path == "/api/v1/test"
        assert evt.method == "DELETE"
        assert evt.event_type == "eaip.gateway.endpoint.unregistered"


class TestApiRequestProcessed:
    def test_is_domain_event(self) -> None:
        assert issubclass(ApiRequestProcessed, DomainEvent)

    def test_fields(self) -> None:
        evt = ApiRequestProcessed(
            request_id="req-1",
            path="/test",
            method="POST",
            status_code=201,
            duration_ms=42.5,
        )
        assert evt.request_id == "req-1"
        assert evt.path == "/test"
        assert evt.method == "POST"
        assert evt.status_code == 201
        assert evt.duration_ms == 42.5
        assert evt.event_type == "eaip.gateway.request.processed"
