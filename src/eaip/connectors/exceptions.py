"""Exception hierarchy for the connector management subsystem."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ConnectorError(EAIPError):
    """Base exception for connector-related failures."""

    default_code = ErrorCode.INTERNAL_ERROR


class ConnectorNotFoundError(ConnectorError):
    """Raised when a connector is not found."""

    default_code = ErrorCode.NOT_FOUND


class ConnectorConfigError(ConnectorError):
    """Raised when connector configuration is invalid."""

    default_code = ErrorCode.CONFIGURATION_INVALID


class ConnectorAuthError(ConnectorError):
    """Raised when connector authentication fails."""

    default_code = ErrorCode.AUTH_FAILED


class ConnectorConnectionError(ConnectorError):
    """Raised when a connector connection fails."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class ConnectorOperationError(ConnectorError):
    """Raised when a connector operation fails."""

    default_code = ErrorCode.GATEWAY_ERROR


class ConnectorSyncError(ConnectorError):
    """Raised when connector synchronization fails."""

    default_code = ErrorCode.GATEWAY_ERROR


class ConnectorHealthError(ConnectorError):
    """Raised when a connector health check fails."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class ConnectorRateLimitError(ConnectorError):
    """Raised when a connector rate limit is exceeded."""

    default_code = ErrorCode.RATE_LIMITED


__all__ = [
    "ConnectorAuthError",
    "ConnectorConfigError",
    "ConnectorConnectionError",
    "ConnectorError",
    "ConnectorHealthError",
    "ConnectorNotFoundError",
    "ConnectorOperationError",
    "ConnectorRateLimitError",
    "ConnectorSyncError",
]
