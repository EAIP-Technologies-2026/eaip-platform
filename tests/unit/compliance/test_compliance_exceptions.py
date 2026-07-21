from __future__ import annotations

from eaip.compliance.exceptions import (
    ComplianceError,
    ControlNotSatisfiedError,
    EvidenceExpiredError,
    RegulationNotFoundError,
)
from eaip.exceptions.base import ErrorCode


class TestComplianceExceptions:
    def test_compliance_error_base(self) -> None:
        err = ComplianceError("base compliance failure")
        assert isinstance(err, ComplianceError)
        assert err.code == ErrorCode.UNKNOWN

    def test_compliance_error_with_context(self) -> None:
        err = ComplianceError("test", context={"regulation": "gdpr"})
        assert err.context["regulation"] == "gdpr"

    def test_regulation_not_found(self) -> None:
        err = RegulationNotFoundError("regulation missing", context={"regulation_id": "gdpr"})
        assert err.code == ErrorCode.NOT_FOUND
        assert err.context["regulation_id"] == "gdpr"

    def test_control_not_satisfied(self) -> None:
        err = ControlNotSatisfiedError("control not met", context={"control_id": "c1"})
        assert err.code == ErrorCode.POLICY_VIOLATION
        assert err.context["control_id"] == "c1"

    def test_evidence_expired(self) -> None:
        err = EvidenceExpiredError("evidence expired", context={"evidence_id": "e1"})
        assert err.code == ErrorCode.VALIDATION_FAILED
        assert err.context["evidence_id"] == "e1"

    def test_to_dict(self) -> None:
        err = ComplianceError("test", code=ErrorCode.INTERNAL_ERROR, context={"a": 1})
        d = err.to_dict()
        assert d["message"] == "test"
        assert d["code"] == "EAIP-0017"
        assert d["context"]["a"] == 1
        assert d["type"] == "ComplianceError"

    def test_regulation_not_found_to_dict(self) -> None:
        err = RegulationNotFoundError("missing", context={"regulation_id": "hipaa"})
        d = err.to_dict()
        assert d["code"] == "EAIP-0003"
        assert d["context"]["regulation_id"] == "hipaa"
