"""Tests for cloudmgr exceptions."""

from __future__ import annotations

from eaip.cloudmgr.exceptions import CloudManagerError, ProviderNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestCloudManagerError:
    def test_base_exception(self) -> None:
        err = CloudManagerError("Cloud error")
        assert isinstance(err, EAIPError)
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert str(err) == "Cloud error"

    def test_with_context(self) -> None:
        err = CloudManagerError("Error", context={"provider": "aws"})
        assert err.context == {"provider": "aws"}


class TestProviderNotFoundError:
    def test_default_code(self) -> None:
        err = ProviderNotFoundError("Provider not found")
        assert isinstance(err, CloudManagerError)
        assert err.code == ErrorCode.PROVIDER_NOT_FOUND

    def test_custom_message(self) -> None:
        err = ProviderNotFoundError("Provider 'aws' not found")
        assert "aws" in str(err)
