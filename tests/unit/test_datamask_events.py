"""Tests for :mod:`eaip.datamask.events`."""

from __future__ import annotations

import pytest

from eaip.datamask.events import (
    AnonymizationCompleted,
    AnonymizationFailed,
    AnonymizationStarted,
    DataClassified,
    MaskingRuleCreated,
    MaskingRuleUpdated,
    PiiDetected,
)
from eaip.datamask.models import (
    ClassificationLevel,
    DataClassificationResult,
    PiiDetectionResult,
)
from eaip.events.event import DomainEvent


class TestMaskingRuleCreated:
    def test_defaults(self) -> None:
        e = MaskingRuleCreated(
            rule_id="r1", rule_name="Email Mask", data_type="email", strategy="mask"
        )
        assert isinstance(e, DomainEvent)
        assert e.event_type == "eaip.datamask.masking_rule.created"
        assert e.rule_id == "r1"
        assert e.data_type == "email"
        assert e.strategy == "mask"

    def test_frozen(self) -> None:
        e = MaskingRuleCreated(rule_id="r1", rule_name="n", data_type="t", strategy="s")
        with pytest.raises((ValueError, TypeError)):
            e.rule_id = "r2"  # type: ignore[misc]


class TestMaskingRuleUpdated:
    def test_defaults(self) -> None:
        e = MaskingRuleUpdated(rule_id="r1", rule_name="Email", changes={"name": "New"})
        assert e.event_type == "eaip.datamask.masking_rule.updated"
        assert e.changes["name"] == "New"


class TestAnonymizationStarted:
    def test_defaults(self) -> None:
        e = AnonymizationStarted(job_id="j1", job_name="job-1", source="db://users", rule_count=2)
        assert e.event_type == "eaip.datamask.anonymization.started"
        assert e.job_id == "j1"
        assert e.rule_count == 2


class TestAnonymizationCompleted:
    def test_defaults(self) -> None:
        e = AnonymizationCompleted(
            job_id="j1",
            job_name="job-1",
            records_processed=10,
            records_skipped=2,
            duration_ms=150.0,
        )
        assert e.event_type == "eaip.datamask.anonymization.completed"
        assert e.records_processed == 10
        assert e.duration_ms == 150.0


class TestAnonymizationFailed:
    def test_defaults(self) -> None:
        e = AnonymizationFailed(job_id="j1", job_name="job-1", error="Something went wrong")
        assert e.event_type == "eaip.datamask.anonymization.failed"
        assert "went wrong" in e.error


class TestPiiDetected:
    def test_defaults(self) -> None:
        result = PiiDetectionResult(id="p1", field_name="email", detected_types=("email",))
        e = PiiDetected(result=result)
        assert e.event_type == "eaip.datamask.pii.detected"
        assert e.result.field_name == "email"


class TestDataClassified:
    def test_defaults(self) -> None:
        result = DataClassificationResult(
            id="c1", data_type="email", classification_level=ClassificationLevel.CONFIDENTIAL
        )
        e = DataClassified(result=result)
        assert e.event_type == "eaip.datamask.data.classified"
        assert e.result.classification_level is ClassificationLevel.CONFIDENTIAL


class TestAllEvents:
    def test_all_have_unique_event_types(self) -> None:
        events = [
            MaskingRuleCreated,
            MaskingRuleUpdated,
            AnonymizationStarted,
            AnonymizationCompleted,
            AnonymizationFailed,
            PiiDetected,
            DataClassified,
        ]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))

    def test_all_are_domain_events(self) -> None:
        events = [
            MaskingRuleCreated(rule_id="r1", rule_name="n", data_type="t", strategy="s"),
            MaskingRuleUpdated(rule_id="r1", rule_name="n", changes={}),
            AnonymizationStarted(job_id="j1", job_name="n", source="s", rule_count=0),
            AnonymizationCompleted(
                job_id="j1", job_name="n", records_processed=0, records_skipped=0
            ),
            AnonymizationFailed(job_id="j1", job_name="n", error="err"),
            PiiDetected(result=PiiDetectionResult(id="p1", field_name="f")),
            DataClassified(
                result=DataClassificationResult(
                    id="c1", data_type="t", classification_level=ClassificationLevel.PUBLIC
                )
            ),
        ]
        for e in events:
            assert isinstance(e, DomainEvent), f"{type(e).__name__} is not a DomainEvent"
