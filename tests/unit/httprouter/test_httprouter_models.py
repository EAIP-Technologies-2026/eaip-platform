"""Tests for :mod:`eaip.httprouter.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.httprouter.models import Route, RouteMatch, RouteStatus, RouterConfig


class TestRoute:
    def test_create_minimal(self) -> None:
        r = Route(id="r1", path="/api/v1/users", target_url="http://backend/users")
        assert r.status is RouteStatus.ACTIVE
        assert r.method == "GET"
        assert r.middleware == ()

    def test_frozen(self) -> None:
        r = Route(id="r1", path="/p", target_url="http://t")
        with pytest.raises(ValidationError):
            r.path = "/changed"


class TestRouteMatch:
    def test_create(self) -> None:
        m = RouteMatch(route_id="r1", request_path="/api/v1/users")
        assert m.priority == 0

    def test_frozen(self) -> None:
        m = RouteMatch(route_id="r1", request_path="/p")
        with pytest.raises(ValidationError):
            m.priority = 1


class TestRouterConfig:
    def test_defaults(self) -> None:
        c = RouterConfig()
        assert c.default_timeout_ms == 5000
        assert c.max_routes == 1000

    def test_frozen(self) -> None:
        c = RouterConfig()
        with pytest.raises(ValidationError):
            c.max_routes = 500


class TestRouteStatus:
    def test_values(self) -> None:
        assert RouteStatus.ACTIVE.value == "active"
        assert RouteStatus.INACTIVE.value == "inactive"


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Route(id="r1", path="/p", target_url="http://t", unknown="x")
