"""Exception hierarchy for the token & authentication service."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode, ErrorSeverity


class AuthError(EAIPError):
    default_code = ErrorCode.AUTH_FAILED
    default_severity = ErrorSeverity.ERROR


class TokenExpiredError(AuthError):
    default_code = ErrorCode.AUTH_FAILED
    default_severity = ErrorSeverity.WARNING


class TokenInvalidError(AuthError):
    default_code = ErrorCode.AUTH_FAILED
    default_severity = ErrorSeverity.WARNING


class TokenRevokedError(AuthError):
    default_code = ErrorCode.AUTH_FAILED
    default_severity = ErrorSeverity.WARNING


class AuthenticationError(AuthError):
    default_code = ErrorCode.AUTH_FAILED
    default_severity = ErrorSeverity.ERROR


class ProviderNotFoundError(AuthError):
    default_code = ErrorCode.PROVIDER_NOT_FOUND
    default_severity = ErrorSeverity.WARNING


class ProviderAlreadyRegisteredError(AuthError):
    default_code = ErrorCode.REGISTRY_DUPLICATE
    default_severity = ErrorSeverity.WARNING


__all__ = [
    "AuthError",
    "AuthenticationError",
    "ProviderAlreadyRegisteredError",
    "ProviderNotFoundError",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenRevokedError",
]
