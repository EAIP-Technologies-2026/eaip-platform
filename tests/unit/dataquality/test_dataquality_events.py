from __future__ import annotations

from eaip.dataquality.events import (
    AnomalyDetected,
    DataQualityEvent,
    QualityCheckExecuted,
    QualityCheckFailed,
    QualityCheckPassed,
    QualityRuleCreated,
    QualityRuleUpdated,
    QualityViolationDetected,
)


class TestDataqualityEvents:
    def test_base_event(self) -> None:
        assert DataQualityEvent.event_type == "eaip.dataquality.event"

    def test_quality_rule_created(self) -> None:
        event = QualityRuleCreated(
            rule_id="r1", name="required_field", rule_type="required", severity="error"
        )
        assert event.event_type == "eaip.dataquality.rule.created"
        assert event.rule_type == "required"

    def test_quality_rule_created_default_severity(self) -> None:
        event = QualityRuleCreated(rule_id="r1", name="test", rule_type="unique")
        assert event.severity == "error"

    def test_quality_rule_updated(self) -> None:
        event = QualityRuleUpdated(rule_id="r1", name="test", changes={"severity": "warning"})
        assert event.event_type == "eaip.dataquality.rule.updated"
        assert event.changes["severity"] == "warning"

    def test_quality_check_executed(self) -> None:
        event = QualityCheckExecuted(
            check_id="c1",
            status="passed",
            total_checks=10,
            passed_checks=10,
            failed_checks=0,
            duration_ms=100.0,
        )
        assert event.event_type == "eaip.dataquality.check.executed"
        assert event.passed_checks == 10

    def test_quality_check_passed(self) -> None:
        event = QualityCheckPassed(check_id="c1", passed_checks=5)
        assert event.event_type == "eaip.dataquality.check.passed"

    def test_quality_check_failed(self) -> None:
        event = QualityCheckFailed(check_id="c1", failed_checks=2, errors=("rule r1 failed",))
        assert event.event_type == "eaip.dataquality.check.failed"
        assert "r1 failed" in event.errors[0]

    def test_quality_violation_detected(self) -> None:
        event = QualityViolationDetected(
            violation_id="v1", rule_id="r1", field="email", severity="error", message="invalid"
        )
        assert event.event_type == "eaip.dataquality.violation.detected"
        assert event.field == "email"

    def test_anomaly_detected(self) -> None:
        event = AnomalyDetected(field="temperature", value=999.0, score=3.5, detail="Outlier")
        assert event.event_type == "eaip.dataquality.anomaly.detected"
        assert event.score == 3.5

    def test_all_frozen(self) -> None:
        import pydantic
        import pytest

        event = QualityRuleCreated(rule_id="r1", name="test", rule_type="required")
        with pytest.raises(pydantic.ValidationError):
            event.rule_id = "r2"  # type: ignore[misc]
