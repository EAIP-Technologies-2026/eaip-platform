"""Exception hierarchy for the service mesh."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class MeshError(EAIPError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


class ServiceNotFoundError(MeshError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class RouteNotFoundError(MeshError):
    default_code = ErrorCode.NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class NoHealthyInstanceError(MeshError):
    default_code = ErrorCode.PROVIDER_UNAVAILABLE
    default_severity = ErrorSeverity.ERROR


class CircuitBreakerOpenError(MeshError):
    default_code = ErrorCode.PROVIDER_UNAVAILABLE
    default_severity = ErrorSeverity.ERROR


class LoadBalancerError(MeshError):
    default_code = ErrorCode.INTERNAL_ERROR
    default_severity = ErrorSeverity.ERROR


__all__ = [
    "CircuitBreakerOpenError",
    "LoadBalancerError",
    "MeshError",
    "NoHealthyInstanceError",
    "RouteNotFoundError",
    "ServiceNotFoundError",
]
