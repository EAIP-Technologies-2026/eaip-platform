"""Tests for fedid exceptions."""

from __future__ import annotations

from eaip.exceptions.base import EAIPError, ErrorCode
from eaip.fedid.exceptions import (
    AuthenticationFailedError,
    FederationError,
    ProviderNotFoundError,
)


class TestFederationError:
    def test_base_exception(self) -> None:
        err = FederationError("Federation error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Federation error"

    def test_with_context(self) -> None:
        err = FederationError("Error", context={"idp": "azure"})
        assert err.context == {"idp": "azure"}


class TestProviderNotFoundError:
    def test_default_code(self) -> None:
        err = ProviderNotFoundError("Provider not found")
        assert isinstance(err, FederationError)
        assert err.code == ErrorCode.PROVIDER_NOT_FOUND

    def test_custom_message(self) -> None:
        err = ProviderNotFoundError("Provider 'azure' not found")
        assert "azure" in str(err)


class TestAuthenticationFailedError:
    def test_default_code(self) -> None:
        err = AuthenticationFailedError("Auth failed")
        assert isinstance(err, FederationError)
        assert err.code == ErrorCode.AUTH_FAILED

    def test_custom_message(self) -> None:
        err = AuthenticationFailedError("Invalid credentials provided")
        assert "Invalid credentials" in str(err)
