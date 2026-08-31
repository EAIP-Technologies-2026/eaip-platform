"""Exception hierarchy for resource optimization."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ResourceOptimizationError(EAIPError):
    """Base exception for resource optimization errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ResourceOptimizationConfigError(ResourceOptimizationError):
    """Raised when the resource optimization configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class ResourceMetricsError(ResourceOptimizationError):
    """Raised when resource metrics operations fail."""

    default_code = ErrorCode.INTERNAL_ERROR


class ResourceRecommendationError(ResourceOptimizationError):
    """Raised when resource recommendation operations fail."""

    default_code = ErrorCode.INTERNAL_ERROR


class ResourceActionError(ResourceOptimizationError):
    """Raised when a resource optimization action fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class ResourceAllocationError(ResourceOptimizationError):
    """Raised when resource allocation operations fail."""

    default_code = ErrorCode.INTERNAL_ERROR


class ResourceDemandForecastError(ResourceOptimizationError):
    """Raised when resource demand forecast operations fail."""

    default_code = ErrorCode.INTERNAL_ERROR


class ResourceConstraintError(ResourceOptimizationError):
    """Raised when resource constraint operations fail."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "ResourceActionError",
    "ResourceAllocationError",
    "ResourceConstraintError",
    "ResourceDemandForecastError",
    "ResourceMetricsError",
    "ResourceOptimizationConfigError",
    "ResourceOptimizationError",
    "ResourceRecommendationError",
]
