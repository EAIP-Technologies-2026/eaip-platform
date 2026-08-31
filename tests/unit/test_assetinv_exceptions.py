"""Tests for :mod:`eaip.assetinv.exceptions`."""

from __future__ import annotations

from eaip.assetinv.exceptions import AssetInventoryError, AssetNotFoundError
from eaip.exceptions.base import ErrorCode


class TestAssetInventoryError:
    def test_base_exception(self) -> None:
        err = AssetInventoryError("asset inventory error")
        assert str(err) == "asset inventory error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestAssetNotFoundError:
    def test_default_code(self) -> None:
        err = AssetNotFoundError("asset not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = AssetNotFoundError("not found")
        assert isinstance(err, AssetInventoryError)
