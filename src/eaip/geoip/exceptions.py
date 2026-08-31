"""Exception hierarchy for Geo-IP service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class GeoIPError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class LookupError(GeoIPError):
    default_code = ErrorCode.PROVIDER_UNAVAILABLE


__all__ = [
    "GeoIPError",
    "LookupError",
]
