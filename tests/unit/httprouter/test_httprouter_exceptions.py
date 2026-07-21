"""Tests for :mod:`eaip.httprouter.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.httprouter.exceptions import RouteNotFoundError, RouterError


class TestRouterExceptionHierarchy:
    def test_router_error_is_eaip_error(self) -> None:
        assert issubclass(RouterError, EAIPError)

    def test_not_found_is_router_error(self) -> None:
        assert issubclass(RouteNotFoundError, RouterError)


class TestErrorCodes:
    def test_router_error_code(self) -> None:
        err = RouterError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_not_found_code(self) -> None:
        err = RouteNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND


class TestErrorMessage:
    def test_message_preserved(self) -> None:
        err = RouteNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        err = RouterError("bad", context={"route_id": "r1"})
        assert err.context["route_id"] == "r1"
