"""Tests for compliance report generator exception hierarchy."""

from __future__ import annotations

from eaip.compliancegen.exceptions import ComplianceGenError, FrameworkNotFoundError
from eaip.exceptions.base import EAIPError, ErrorCode


class TestComplianceGenError:
    def test_is_eaip_error(self) -> None:
        err = ComplianceGenError("generic error")
        assert isinstance(err, EAIPError)

    def test_default_code(self) -> None:
        err = ComplianceGenError("test")
        assert err.code == ErrorCode.UNKNOWN


class TestFrameworkNotFoundError:
    def test_inherits_compliance_gen_error(self) -> None:
        err = FrameworkNotFoundError("not found")
        assert isinstance(err, ComplianceGenError)

    def test_default_code(self) -> None:
        err = FrameworkNotFoundError("missing")
        assert err.code == ErrorCode.NOT_FOUND
