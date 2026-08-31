"""Tests for :mod:`eaip.datamask.models`."""

from __future__ import annotations

import pytest

from eaip.datamask.models import (
    AnonymizationJob,
    ClassificationLevel,
    DataClassificationResult,
    DataType,
    JobStatus,
    MaskingConfig,
    MaskingRule,
    MaskingStrategy,
    PiiDetectionResult,
)


class TestMaskingRule:
    def test_defaults(self) -> None:
        r = MaskingRule(
            id="r1",
            name="Email Mask",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        assert r.id == "r1"
        assert r.name == "Email Mask"
        assert r.data_type is DataType.EMAIL
        assert r.strategy is MaskingStrategy.MASK
        assert r.mask_character == "*"
        assert r.preserve_length is True
        assert r.preserve_prefix_count == 0
        assert r.substitution_dict == {}
        assert r.enabled is True
        assert r.tags == ()
        assert r.metadata == {}

    def test_with_all_fields(self) -> None:
        r = MaskingRule(
            id="r2",
            name="SSN Mask",
            field_pattern="ssn",
            data_type=DataType.SSN,
            strategy=MaskingStrategy.REDACT,
            mask_character="#",
            preserve_length=False,
            preserve_prefix_count=4,
            substitution_dict={"123-45-6789": "XXX-XX-XXXX"},
            enabled=False,
            tags=("pii", "ssn"),
            metadata={"env": "prod"},
        )
        assert r.data_type is DataType.SSN
        assert r.strategy is MaskingStrategy.REDACT
        assert r.mask_character == "#"
        assert r.preserve_length is False
        assert r.preserve_prefix_count == 4
        assert r.substitution_dict["123-45-6789"] == "XXX-XX-XXXX"
        assert r.enabled is False
        assert "pii" in r.tags
        assert r.metadata["env"] == "prod"

    def test_frozen(self) -> None:
        r = MaskingRule(
            id="r1",
            name="n",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.MASK,
        )
        with pytest.raises((ValueError, TypeError)):
            r.name = "new-name"  # type: ignore[misc]

    def test_data_type_values(self) -> None:
        assert DataType.EMAIL.value == "email"
        assert DataType.PHONE.value == "phone"
        assert DataType.SSN.value == "ssn"
        assert DataType.CREDIT_CARD.value == "creditcard"
        assert DataType.NAME.value == "name"
        assert DataType.ADDRESS.value == "address"
        assert DataType.IP.value == "ip"
        assert DataType.CUSTOM.value == "custom"

    def test_strategy_values(self) -> None:
        assert MaskingStrategy.MASK.value == "mask"
        assert MaskingStrategy.TRUNCATE.value == "truncate"
        assert MaskingStrategy.HASH.value == "hash"
        assert MaskingStrategy.REDACT.value == "redact"
        assert MaskingStrategy.ENCRYPT.value == "encrypt"
        assert MaskingStrategy.SUBSTITUTE.value == "substitute"


class TestAnonymizationJob:
    def test_defaults(self) -> None:
        j = AnonymizationJob(id="j1", name="test-job", source="db://users")
        assert j.status is JobStatus.PENDING
        assert j.records_processed == 0
        assert j.records_skipped == 0
        assert j.started_at is None
        assert j.completed_at is None
        assert j.error is None
        assert j.metadata == {}

    def test_with_rules(self) -> None:
        r = MaskingRule(
            id="r1",
            name="Email",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        j = AnonymizationJob(
            id="j2",
            name="job-2",
            source="s3://data",
            rules=(r,),
            status=JobStatus.RUNNING,
            records_processed=10,
        )
        assert j.status is JobStatus.RUNNING
        assert len(j.rules) == 1
        assert j.rules[0].id == "r1"
        assert j.records_processed == 10

    def test_status_values(self) -> None:
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"

    def test_frozen(self) -> None:
        j = AnonymizationJob(id="j1", name="n", source="s")
        with pytest.raises((ValueError, TypeError)):
            j.name = "new"  # type: ignore[misc]


class TestPiiDetectionResult:
    def test_defaults(self) -> None:
        r = PiiDetectionResult(id="p1", field_name="email")
        assert r.detected_types == ()
        assert r.confidence == 0.0
        assert r.occurrence_count == 0
        assert r.sample_values == ()
        assert r.location == ""
        assert r.metadata == {}

    def test_with_all_fields(self) -> None:
        r = PiiDetectionResult(
            id="p2",
            field_name="user_email",
            detected_types=("email",),
            confidence=0.95,
            occurrence_count=3,
            sample_values=("user@example.com",),
            location="body.user_email",
            metadata={"source": "form"},
        )
        assert "email" in r.detected_types
        assert r.confidence == 0.95
        assert r.occurrence_count == 3
        assert r.sample_values[0] == "user@example.com"

    def test_frozen(self) -> None:
        r = PiiDetectionResult(id="p1", field_name="f")
        with pytest.raises((ValueError, TypeError)):
            r.field_name = "new"  # type: ignore[misc]


class TestDataClassificationResult:
    def test_defaults(self) -> None:
        c = DataClassificationResult(
            id="c1", data_type="email", classification_level=ClassificationLevel.CONFIDENTIAL
        )
        assert c.findings == ()
        assert c.score == 0.0
        assert c.metadata == {}

    def test_with_findings(self) -> None:
        c = DataClassificationResult(
            id="c2",
            data_type="email|phone",
            classification_level=ClassificationLevel.RESTRICTED,
            findings=("email", "phone"),
            score=0.85,
            metadata={"source": "scan"},
        )
        assert c.score == 0.85
        assert len(c.findings) == 2

    def test_level_values(self) -> None:
        assert ClassificationLevel.PUBLIC.value == "public"
        assert ClassificationLevel.INTERNAL.value == "internal"
        assert ClassificationLevel.CONFIDENTIAL.value == "confidential"
        assert ClassificationLevel.RESTRICTED.value == "restricted"
        assert ClassificationLevel.CRITICAL.value == "critical"

    def test_frozen(self) -> None:
        c = DataClassificationResult(
            id="c1", data_type="t", classification_level=ClassificationLevel.PUBLIC
        )
        with pytest.raises((ValueError, TypeError)):
            c.data_type = "new"  # type: ignore[misc]


class TestMaskingConfig:
    def test_defaults(self) -> None:
        c = MaskingConfig()
        assert c.default_mask_char == "*"
        assert c.enable_pii_detection is True
        assert c.enable_audit_logging is True
        assert c.max_parallel_jobs == 4
        assert c.field_discovery_enabled is True

    def test_custom_values(self) -> None:
        c = MaskingConfig(
            default_mask_char="#",
            enable_pii_detection=False,
            enable_audit_logging=False,
            max_parallel_jobs=8,
            field_discovery_enabled=False,
        )
        assert c.default_mask_char == "#"
        assert c.enable_pii_detection is False
        assert c.max_parallel_jobs == 8
        assert c.field_discovery_enabled is False

    def test_frozen(self) -> None:
        c = MaskingConfig()
        with pytest.raises((ValueError, TypeError)):
            c.max_parallel_jobs = 10  # type: ignore[misc]
