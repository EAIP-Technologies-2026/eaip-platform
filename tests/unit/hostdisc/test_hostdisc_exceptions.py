"""Tests for :mod:`eaip.hostdisc.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.hostdisc.exceptions import DiscoveryError, HostNotFoundError


class TestHostDiscExceptionHierarchy:
    def test_discovery_error_is_eaip_error(self) -> None:
        assert issubclass(DiscoveryError, EAIPError)

    def test_not_found_is_discovery_error(self) -> None:
        assert issubclass(HostNotFoundError, DiscoveryError)


class TestErrorCodes:
    def test_discovery_error_code(self) -> None:
        err = DiscoveryError("test")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_not_found_code(self) -> None:
        err = HostNotFoundError("not found")
        assert err.code == ErrorCode.NOT_FOUND


class TestErrorMessage:
    def test_message_preserved(self) -> None:
        err = HostNotFoundError("Custom message")
        assert str(err) == "Custom message"

    def test_context_supported(self) -> None:
        err = DiscoveryError("bad", context={"host_id": "h1"})
        assert err.context["host_id"] == "h1"
