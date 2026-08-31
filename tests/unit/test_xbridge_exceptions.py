"""Tests for :mod:`eaip.xbridge.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.xbridge.exceptions import (
    BridgeError,
    ConnectorNotFoundError,
    MessageRoutingError,
)


class TestBridgeError:
    def test_base_exception(self) -> None:
        err = BridgeError("bridge failed")
        assert str(err) == "bridge failed"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestConnectorNotFoundError:
    def test_default_code(self) -> None:
        err = ConnectorNotFoundError("connector not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = ConnectorNotFoundError("not found")
        assert isinstance(err, BridgeError)


class TestMessageRoutingError:
    def test_default_code(self) -> None:
        err = MessageRoutingError("routing failed")
        assert err.code == ErrorCode.GATEWAY_ERROR
