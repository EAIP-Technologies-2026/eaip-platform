"""Provider routing exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ProviderRoutingError(EAIPError):
    """Base exception for all provider routing errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ProviderRouteNotFoundError(ProviderRoutingError):
    """Raised when a requested route is not found."""

    default_code = ErrorCode.NOT_FOUND


class ProviderRouteConfigError(ProviderRoutingError):
    """Raised when route configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class ProviderRouteEvaluationError(ProviderRoutingError):
    """Raised when a route evaluation fails."""

    default_code = ErrorCode.POLICY_VIOLATION


class ProviderEndpointUnavailableError(ProviderRoutingError):
    """Raised when a provider endpoint is unavailable."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class ProviderFallbackError(ProviderRoutingError):
    """Raised when all fallback routes are exhausted."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class ProviderLoadBalancerError(ProviderRoutingError):
    """Raised when load balancing encounters an error."""

    default_code = ErrorCode.INTERNAL_ERROR


class ProviderRouteMetricsError(ProviderRoutingError):
    """Raised when metrics collection fails."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "ProviderEndpointUnavailableError",
    "ProviderFallbackError",
    "ProviderLoadBalancerError",
    "ProviderRouteConfigError",
    "ProviderRouteEvaluationError",
    "ProviderRouteMetricsError",
    "ProviderRouteNotFoundError",
    "ProviderRoutingError",
]
