from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.ws.exceptions import (
    ChannelNotFoundError,
    ConnectionNotFoundError,
    SubscriptionError,
    WsError,
)


class TestWsExceptions:
    def test_ws_error_base(self) -> None:
        err = WsError("base error")
        assert isinstance(err, WsError)
        assert err.code == ErrorCode.GATEWAY_ERROR

    def test_ws_error_with_context(self) -> None:
        err = WsError("test", context={"key": "val"})
        assert err.context["key"] == "val"

    def test_ws_error_with_code(self) -> None:
        err = WsError("test", code=ErrorCode.NOT_FOUND)
        assert err.code == ErrorCode.NOT_FOUND

    def test_connection_not_found(self) -> None:
        err = ConnectionNotFoundError("connection missing", context={"connection_id": "c1"})
        assert err.code == ErrorCode.NOT_FOUND
        assert err.context["connection_id"] == "c1"

    def test_channel_not_found(self) -> None:
        err = ChannelNotFoundError("channel missing", context={"channel_id": "ch1"})
        assert err.code == ErrorCode.NOT_FOUND
        assert err.context["channel_id"] == "ch1"

    def test_subscription_error(self) -> None:
        err = SubscriptionError("subscription failed", context={"user_id": "u1"})
        assert err.code == ErrorCode.POLICY_VIOLATION
        assert err.context["user_id"] == "u1"

    def test_subscription_error_with_cause(self) -> None:
        cause = ValueError("underlying")
        err = SubscriptionError("failed", cause=cause)
        assert err.__cause__ is cause

    def test_to_dict(self) -> None:
        err = WsError("test", code=ErrorCode.GATEWAY_ERROR, context={"a": 1})
        d = err.to_dict()
        assert d["message"] == "test"
        assert d["code"] == "EAIP-0018"
        assert d["context"]["a"] == 1
