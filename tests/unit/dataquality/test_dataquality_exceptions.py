from __future__ import annotations

from eaip.dataquality.exceptions import (
    DataQualityError,
    QualityCheckError,
    QualityCheckNotFoundError,
    QualityRuleNotFoundError,
    ValidationError,
)
from eaip.exceptions.base import ErrorCode


class TestDataqualityExceptions:
    def test_base(self) -> None:
        err = DataQualityError("base")
        assert err.code == ErrorCode.UNKNOWN

    def test_quality_rule_not_found(self) -> None:
        err = QualityRuleNotFoundError("rule missing", context={"rule_id": "r1"})
        assert err.code == ErrorCode.NOT_FOUND
        assert err.context["rule_id"] == "r1"

    def test_quality_check_not_found(self) -> None:
        err = QualityCheckNotFoundError("check missing", context={"check_id": "c1"})
        assert err.code == ErrorCode.NOT_FOUND

    def test_quality_check_error(self) -> None:
        err = QualityCheckError("execution failed", context={"check_id": "c1"})
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_validation_error(self) -> None:
        err = ValidationError("validation failed", context={"field": "email"})
        assert err.code == ErrorCode.VALIDATION_FAILED

    def test_with_cause(self) -> None:
        cause = ValueError("root")
        err = DataQualityError("msg", cause=cause)
        assert err.__cause__ is cause

    def test_to_dict(self) -> None:
        err = QualityRuleNotFoundError("missing", context={"rule_id": "r1"})
        d = err.to_dict()
        assert d["type"] == "QualityRuleNotFoundError"
        assert d["code"] == "EAIP-0003"

    def test_inheritance(self) -> None:
        assert issubclass(QualityRuleNotFoundError, DataQualityError)
        assert issubclass(QualityCheckNotFoundError, DataQualityError)
        assert issubclass(QualityCheckError, DataQualityError)
        assert issubclass(ValidationError, DataQualityError)

    def test_with_context(self) -> None:
        err = DataQualityError("error", context={"key": "val"})
        assert err.context["key"] == "val"

    def test_with_code(self) -> None:
        err = DataQualityError("error", code=ErrorCode.POLICY_VIOLATION)
        assert err.code == ErrorCode.POLICY_VIOLATION
