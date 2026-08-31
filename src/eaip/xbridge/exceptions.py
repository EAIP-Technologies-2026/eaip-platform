"""Exception hierarchy for the cross-platform connector bridge."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class BridgeError(EAIPError):
    """Base exception for bridge-related failures."""

    default_code = ErrorCode.INTERNAL_ERROR


class ConnectorNotFoundError(BridgeError):
    """Raised when a connector is not found."""

    default_code = ErrorCode.NOT_FOUND


class MessageRoutingError(BridgeError):
    """Raised when message routing fails."""

    default_code = ErrorCode.GATEWAY_ERROR


__all__ = [
    "BridgeError",
    "ConnectorNotFoundError",
    "MessageRoutingError",
]
