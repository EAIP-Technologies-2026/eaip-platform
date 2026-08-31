"""Provider-specific exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class ProviderError(EAIPError):
    """Base for provider-related failures."""

    default_code = ErrorCode.PROVIDER_UNAVAILABLE


class ProviderNotFoundError(EAIPError):
    """Raised when a requested provider is not in the registry."""

    default_code = ErrorCode.PROVIDER_NOT_FOUND


class ProviderTimeoutError(EAIPError):
    """Raised when a provider request times out."""

    default_code = ErrorCode.PROVIDER_TIMEOUT


class ModelNotFoundError(EAIPError):
    """Raised when a requested model is not found in any provider."""

    default_code = ErrorCode.MODEL_NOT_FOUND


__all__ = [
    "ModelNotFoundError",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderTimeoutError",
]
