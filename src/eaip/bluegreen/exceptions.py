"""Exception hierarchy for blue-green deployment management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class BlueGreenError(EAIPError):
    """Base exception for blue-green deployment errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class SwitchError(BlueGreenError):
    """Raised when a deployment switch operation fails."""

    default_code = ErrorCode.GATEWAY_ERROR


__all__ = [
    "BlueGreenError",
    "SwitchError",
]
