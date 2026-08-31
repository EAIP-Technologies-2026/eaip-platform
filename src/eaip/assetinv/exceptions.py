"""Exception hierarchy for asset inventory."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class AssetInventoryError(EAIPError):
    """Base exception for asset inventory errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class AssetNotFoundError(AssetInventoryError):
    """Raised when an asset is not found."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "AssetInventoryError",
    "AssetNotFoundError",
]
