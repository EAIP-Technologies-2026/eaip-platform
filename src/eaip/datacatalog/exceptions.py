"""Exception hierarchy for the enterprise data catalog."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode


class CatalogError(EAIPError):
    """Base exception for data catalog errors."""

    default_code = ErrorCode.INTERNAL_ERROR


class AssetNotFoundError(CatalogError):
    """Raised when a data asset is not found in the catalog."""

    default_code = ErrorCode.NOT_FOUND


__all__ = [
    "AssetNotFoundError",
    "CatalogError",
]
