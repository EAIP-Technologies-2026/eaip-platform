"""Exception hierarchy for the admin_api package."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AdminApiError(EAIPError):
    """Base exception for all admin-api errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ApiDefinitionNotFoundError(AdminApiError):
    """Raised when a requested API definition does not exist."""

    default_code = ErrorCode.NOT_FOUND


class ApiEndpointError(AdminApiError):
    """Raised when an API endpoint operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class ApiVersionError(AdminApiError):
    """Raised when an API version operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class ApiClientError(AdminApiError):
    """Raised when an API client operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class ApiAuthError(AdminApiError):
    """Raised when API authentication fails."""

    default_code = ErrorCode.AUTH_FAILED


class ApiRateLimitError(AdminApiError):
    """Raised when an API rate limit is exceeded."""

    default_code = ErrorCode.RATE_LIMITED


class ApiUsageError(AdminApiError):
    """Raised when a usage metric operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


class ApiSpecificationError(AdminApiError):
    """Raised when an API specification operation fails."""

    default_code = ErrorCode.INTERNAL_ERROR


__all__ = [
    "AdminApiError",
    "ApiAuthError",
    "ApiClientError",
    "ApiDefinitionNotFoundError",
    "ApiEndpointError",
    "ApiRateLimitError",
    "ApiSpecificationError",
    "ApiUsageError",
    "ApiVersionError",
]
