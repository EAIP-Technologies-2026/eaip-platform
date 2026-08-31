"""WebSocket exception classes."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class WsError(EAIPError):
    """Base exception for WebSocket errors."""

    default_code = ErrorCode.GATEWAY_ERROR


class ConnectionNotFoundError(WsError):
    """Raised when a WebSocket connection is not found."""

    default_code = ErrorCode.NOT_FOUND


class ChannelNotFoundError(WsError):
    """Raised when a channel is not found."""

    default_code = ErrorCode.NOT_FOUND


class SubscriptionError(WsError):
    """Raised when a subscription operation fails."""

    default_code = ErrorCode.POLICY_VIOLATION


__all__ = [
    "ChannelNotFoundError",
    "ConnectionNotFoundError",
    "SubscriptionError",
    "WsError",
]
