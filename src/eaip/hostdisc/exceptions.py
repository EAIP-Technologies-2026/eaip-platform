"""Exception hierarchy for host discovery."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class DiscoveryError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class HostNotFoundError(DiscoveryError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "DiscoveryError",
    "HostNotFoundError",
]
