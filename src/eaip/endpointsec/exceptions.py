"""Exception hierarchy for endpoint security scanning."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class EndpointScanError(EAIPError):
    """Base exception for endpoint security scanning errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class EndpointNotFoundError(EndpointScanError):
    """Raised when an endpoint is not found."""

    default_code = ErrorCode.ENDPOINT_NOT_FOUND


__all__ = [
    "EndpointNotFoundError",
    "EndpointScanError",
]
