from __future__ import annotations

import pydantic
import pytest

from eaip.dataquality.models import (
    DataQualityConfig,
    QualityCheck,
    QualityResult,
    QualityRule,
    QualityViolation,
)


class TestDataQualityConfig:
    def test_defaults(self) -> None:
        cfg = DataQualityConfig()
        assert cfg.default_severity == "warning"
        assert cfg.max_violations_per_check == 1000
        assert cfg.enable_auto_remediate is False
        assert cfg.retention_days == 90
        assert cfg.notify_on_failure is True

    def test_frozen(self) -> None:
        cfg = DataQualityConfig()
        with pytest.raises(pydantic.ValidationError):
            cfg.default_severity = "error"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            DataQualityConfig(unknown="x")  # type: ignore[call-arg]

    def test_invalid_severity(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            DataQualityConfig(default_severity="critical")

    def test_range_validation(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            DataQualityConfig(max_violations_per_check=0)


class TestQualityRule:
    def test_defaults(self) -> None:
        rule = QualityRule(id="r1", name="required_field", field="email", rule_type="required")
        assert rule.description == ""
        assert rule.params == {}
        assert rule.severity == "error"
        assert rule.enabled is True
        assert rule.tags == ()
        assert rule.metadata == {}

    def test_frozen(self) -> None:
        rule = QualityRule(id="r1", name="test", field="x", rule_type="required")
        with pytest.raises(pydantic.ValidationError):
            rule.name = "changed"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            QualityRule(id="r1", name="test", field="x", rule_type="required", unknown="x")  # type: ignore[call-arg]

    def test_invalid_rule_type(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            QualityRule(id="r1", name="test", field="x", rule_type="invalid")

    def test_all_rule_types(self) -> None:
        for t in ("required", "unique", "range", "pattern", "type", "custom"):
            rule = QualityRule(id="r1", name="test", field="x", rule_type=t)
            assert rule.rule_type == t

    def test_all_severities(self) -> None:
        for s in ("error", "warning", "info"):
            rule = QualityRule(id="r1", name="test", field="x", rule_type="required", severity=s)
            assert rule.severity == s

    def test_with_params(self) -> None:
        rule = QualityRule(
            id="r1",
            name="range_check",
            field="age",
            rule_type="range",
            params={"min": 0, "max": 150},
        )
        assert rule.params["min"] == 0
        assert rule.params["max"] == 150


class TestQualityCheck:
    def test_defaults(self) -> None:
        check = QualityCheck(id="c1", name="daily_check")
        assert check.rules == ()
        assert check.schedule_cron == ""
        assert check.target == ""
        assert check.status == "active"
        assert check.metadata == {}

    def test_frozen(self) -> None:
        check = QualityCheck(id="c1", name="test")
        with pytest.raises(pydantic.ValidationError):
            check.status = "paused"  # type: ignore[misc]

    def test_invalid_status(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            QualityCheck(id="c1", name="test", status="invalid")

    def test_with_rules(self) -> None:
        check = QualityCheck(
            id="c1",
            name="full_check",
            rules=("r1", "r2"),
            schedule_cron="0 0 * * *",
            target="db.users",
        )
        assert check.rules == ("r1", "r2")
        assert check.schedule_cron == "0 0 * * *"
        assert check.target == "db.users"


class TestQualityResult:
    def test_defaults(self) -> None:
        result = QualityResult(id="res1", check_id="c1", status="passed")
        assert result.total_checks == 0
        assert result.passed_checks == 0
        assert result.failed_checks == 0
        assert result.errors == ()
        assert result.duration_ms == 0.0

    def test_frozen(self) -> None:
        result = QualityResult(id="res1", check_id="c1", status="passed")
        with pytest.raises(pydantic.ValidationError):
            result.status = "failed"  # type: ignore[misc]

    def test_invalid_status(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            QualityResult(id="res1", check_id="c1", status="unknown")

    def test_failed_result(self) -> None:
        result = QualityResult(
            id="res1",
            check_id="c1",
            status="failed",
            total_checks=5,
            passed_checks=2,
            failed_checks=3,
        )
        assert result.failed_checks == 3
        assert result.total_checks == 5

    def test_error_result(self) -> None:
        result = QualityResult(id="res1", check_id="c1", status="error", errors=("timeout",))
        assert result.errors == ("timeout",)


class TestQualityViolation:
    def test_defaults(self) -> None:
        v = QualityViolation(id="v1", rule_id="r1")
        assert v.record_id == ""
        assert v.field == ""
        assert v.value is None
        assert v.expected is None
        assert v.severity == "error"
        assert v.message == ""

    def test_frozen(self) -> None:
        v = QualityViolation(id="v1", rule_id="r1")
        with pytest.raises(pydantic.ValidationError):
            v.severity = "warning"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            QualityViolation(id="v1", rule_id="r1", unknown="x")  # type: ignore[call-arg]

    def test_with_data(self) -> None:
        v = QualityViolation(
            id="v1",
            rule_id="r1",
            record_id="rec1",
            field="email",
            value="bad",
            expected="valid email",
            severity="warning",
            message="Invalid format",
        )
        assert v.field == "email"
        assert v.value == "bad"
        assert v.expected == "valid email"
        assert v.severity == "warning"
        assert v.message == "Invalid format"
