"""Tests for :mod:`eaip.httprouter.events`."""

from __future__ import annotations

import pytest

from eaip.httprouter.events import (
    RequestRouted,
    RouteDeactivated,
    RouteRegistered,
    RouteUpdated,
)


class TestRouteRegistered:
    def test_create(self) -> None:
        e = RouteRegistered(
            route_id="r1", path="/api/v1/users", method="GET", target_url="http://backend/users"
        )
        assert e.event_type == "eaip.httprouter.route.registered"

    def test_frozen(self) -> None:
        e = RouteRegistered(route_id="r1", path="/p", method="GET", target_url="t")
        with pytest.raises(ValueError):
            e.route_id = "r2"


class TestRouteUpdated:
    def test_create(self) -> None:
        e = RouteUpdated(route_id="r1", changes={"path": "/new"})
        assert e.event_type == "eaip.httprouter.route.updated"


class TestRouteDeactivated:
    def test_create(self) -> None:
        e = RouteDeactivated(route_id="r1", reason="maintenance")
        assert e.event_type == "eaip.httprouter.route.deactivated"


class TestRequestRouted:
    def test_create(self) -> None:
        e = RequestRouted(
            route_id="r1",
            request_path="/api/v1/users",
            method="GET",
            target_url="http://backend/users",
        )
        assert e.event_type == "eaip.httprouter.request.routed"


def test_all_events_have_unique_types() -> None:
    types = [
        RouteRegistered(route_id="r", path="/p", method="GET", target_url="t").event_type,
        RouteUpdated(route_id="r").event_type,
        RouteDeactivated(route_id="r").event_type,
        RequestRouted(route_id="r", request_path="/p", method="GET", target_url="t").event_type,
    ]
    assert len(types) == len(set(types))
