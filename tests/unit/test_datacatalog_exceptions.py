"""Tests for datacatalog exceptions."""

from __future__ import annotations

from eaip.datacatalog.exceptions import AssetNotFoundError, CatalogError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestCatalogError:
    def test_base_exception(self) -> None:
        err = CatalogError("Catalog error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Catalog error"

    def test_with_context(self) -> None:
        err = CatalogError("Error", context={"source": "src1"})
        assert err.context == {"source": "src1"}


class TestAssetNotFoundError:
    def test_default_code(self) -> None:
        err = AssetNotFoundError("Asset not found")
        assert isinstance(err, CatalogError)
        assert err.code == ErrorCode.NOT_FOUND

    def with_custom_message(self) -> None:
        err = AssetNotFoundError("Asset 'xyz' not found")
        assert "xyz" in str(err)
