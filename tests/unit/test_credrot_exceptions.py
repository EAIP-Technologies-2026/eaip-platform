"""Tests for :mod:`eaip.credrot.exceptions`."""

from __future__ import annotations

from eaip.credrot.exceptions import CredentialNotFoundError, CredRotError
from eaip.exceptions import ErrorCode


class TestCredRotError:
    def test_default_code(self) -> None:
        err = CredRotError("Rotation failed")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_with_context(self) -> None:
        err = CredRotError("Failed", context={"credential_id": "c1"})
        assert err.context["credential_id"] == "c1"


class TestCredentialNotFoundError:
    def test_default_code(self) -> None:
        err = CredentialNotFoundError("Not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        assert issubclass(CredentialNotFoundError, CredRotError)
