from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.marketplace.exceptions import (
    DependencyNotSatisfiedError,
    MarketplaceError,
    PackageAlreadyInstalledError,
    PackageNotCompatibleError,
    PackageNotFoundError,
)


class TestMarketplaceExceptions:
    def test_marketplace_error_base(self) -> None:
        err = MarketplaceError("base error")
        assert isinstance(err, MarketplaceError)
        assert err.code == ErrorCode.UNKNOWN

    def test_marketplace_error_with_context(self) -> None:
        err = MarketplaceError("test", context={"key": "val"})
        assert err.context["key"] == "val"

    def test_marketplace_error_with_code(self) -> None:
        err = MarketplaceError("test", code=ErrorCode.NOT_FOUND)
        assert err.code == ErrorCode.NOT_FOUND

    def test_package_not_found(self) -> None:
        err = PackageNotFoundError("missing", context={"package_id": "pkg-1"})
        assert err.code == ErrorCode.NOT_FOUND
        assert err.context["package_id"] == "pkg-1"

    def test_package_already_installed(self) -> None:
        err = PackageAlreadyInstalledError("already installed", context={"package_id": "pkg-1"})
        assert err.code == ErrorCode.REGISTRY_DUPLICATE
        assert err.context["package_id"] == "pkg-1"

    def test_package_not_compatible(self) -> None:
        err = PackageNotCompatibleError("not compatible", context={"package_id": "pkg-1"})
        assert err.code == ErrorCode.VALIDATION_FAILED
        assert err.context["package_id"] == "pkg-1"

    def test_dependency_not_satisfied(self) -> None:
        err = DependencyNotSatisfiedError("dependency missing", context={"dependency": "dep-1"})
        assert err.code == ErrorCode.DEPENDENCY_MISSING
        assert err.context["dependency"] == "dep-1"

    def test_package_not_found_with_cause(self) -> None:
        cause = ValueError("underlying")
        err = PackageNotFoundError("missing", cause=cause)
        assert err.__cause__ is cause

    def test_to_dict(self) -> None:
        err = MarketplaceError("test", code=ErrorCode.UNKNOWN, context={"a": 1})
        d = err.to_dict()
        assert d["message"] == "test"
        assert d["context"]["a"] == 1
