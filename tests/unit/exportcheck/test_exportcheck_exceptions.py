"""Tests for :mod:`eaip.exportcheck.exceptions`."""

from __future__ import annotations

from eaip.exceptions.base import ErrorCode
from eaip.exportcheck.exceptions import ComplianceCheckError, PartyNotFoundError


class TestComplianceCheckError:
    def test_base_exception(self) -> None:
        err = ComplianceCheckError("compliance error")
        assert str(err) == "compliance error"
        assert err.code == ErrorCode.INTERNAL_ERROR


class TestPartyNotFoundError:
    def test_default_code(self) -> None:
        err = PartyNotFoundError("party not found")
        assert err.code == ErrorCode.NOT_FOUND

    def test_inheritance(self) -> None:
        err = PartyNotFoundError("not found")
        assert isinstance(err, ComplianceCheckError)
