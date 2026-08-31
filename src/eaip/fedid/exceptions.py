"""Exception hierarchy for federated identity."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class FederationError(EAIPError):
    """Base exception for federation errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ProviderNotFoundError(FederationError):
    """Raised when an identity provider is not found."""

    default_code = ErrorCode.PROVIDER_NOT_FOUND


class AuthenticationFailedError(FederationError):
    """Raised when authentication via a federated provider fails."""

    default_code = ErrorCode.AUTH_FAILED


__all__ = [
    "AuthenticationFailedError",
    "FederationError",
    "ProviderNotFoundError",
]
