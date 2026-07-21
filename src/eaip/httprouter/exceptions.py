"""Exception hierarchy for HTTP request router."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class RouterError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR


class RouteNotFoundError(RouterError):
    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "RouteNotFoundError",
    "RouterError",
]
