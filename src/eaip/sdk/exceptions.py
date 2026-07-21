"""SDK-specific exception hierarchy."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class SdkError(EAIPError):
    """Base exception for SDK-package errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class SdkNotFoundError(SdkError):
    """Raised when an SDK definition is not found."""

    default_code = ErrorCode.SDK_NOT_FOUND


class BuildError(SdkError):
    """Raised when an SDK build operation fails."""

    default_code = ErrorCode.SDK_BUILD_ERROR


class ClientNotFoundError(SdkError):
    """Raised when an API client is not found."""

    default_code = ErrorCode.SDK_CLIENT_NOT_FOUND


class ClientExpiredError(SdkError):
    """Raised when an API client has expired."""

    default_code = ErrorCode.SDK_CLIENT_EXPIRED


class GenerationError(SdkError):
    """Raised when client code generation fails."""

    default_code = ErrorCode.SDK_GENERATION_ERROR


class LanguageNotSupportedError(SdkError):
    """Raised when a requested language is not supported for generation."""

    default_code = ErrorCode.SDK_LANGUAGE_NOT_SUPPORTED
