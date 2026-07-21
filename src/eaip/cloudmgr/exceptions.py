"""Exception hierarchy for cloud resource management."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CloudManagerError(EAIPError):
    """Base exception for cloud manager errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class ProviderNotFoundError(CloudManagerError):
    """Raised when a cloud provider is not found."""

    default_code = ErrorCode.PROVIDER_NOT_FOUND


__all__ = [
    "CloudManagerError",
    "ProviderNotFoundError",
]
