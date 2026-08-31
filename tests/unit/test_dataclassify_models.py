"""Tests for :mod:`eaip.dataclassify.models`."""

from __future__ import annotations

import pytest

from eaip.dataclassify.models import (
    ClassificationResult,
    ClassifierConfig,
    DataCategory,
    DataClass,
)


class TestDataClass:
    def test_defaults(self) -> None:
        c = DataClass(id="dc1", name="SSN", category=DataCategory.RESTRICTED)
        assert c.id == "dc1"
        assert c.name == "SSN"
        assert c.description == ""
        assert c.pattern == ""
        assert c.category is DataCategory.RESTRICTED
        assert c.priority == 0

    def test_with_all_fields(self) -> None:
        c = DataClass(
            id="dc2",
            name="Email",
            description="Email addresses",
            pattern=".*@.*",
            category=DataCategory.CONFIDENTIAL,
            priority=10,
        )
        assert c.description == "Email addresses"
        assert c.pattern == ".*@.*"
        assert c.priority == 10

    def test_frozen(self) -> None:
        c = DataClass(id="dc1", name="N", category=DataCategory.PUBLIC)
        with pytest.raises((ValueError, TypeError)):
            c.name = "new"  # type: ignore[misc]

    def test_category_values(self) -> None:
        assert DataCategory.PUBLIC.value == "public"
        assert DataCategory.INTERNAL.value == "internal"
        assert DataCategory.CONFIDENTIAL.value == "confidential"
        assert DataCategory.RESTRICTED.value == "restricted"


class TestClassificationResult:
    def test_defaults(self) -> None:
        r = ClassificationResult(id="cr1", resource_id="res-1")
        assert r.detected_classes == ()
        assert r.confidence == 0.0

    def test_with_classes(self) -> None:
        r = ClassificationResult(
            id="cr2",
            resource_id="res-2",
            detected_classes=("SSN", "PII"),
            confidence=0.95,
        )
        assert len(r.detected_classes) == 2
        assert r.confidence == 0.95

    def test_frozen(self) -> None:
        r = ClassificationResult(id="cr1", resource_id="r")
        with pytest.raises((ValueError, TypeError)):
            r.resource_id = "new"  # type: ignore[misc]


class TestClassifierConfig:
    def test_defaults(self) -> None:
        c = ClassifierConfig()
        assert c.max_rules == 100
        assert c.confidence_threshold == 0.7
        assert c.enable_auto_classify is True

    def test_custom_values(self) -> None:
        c = ClassifierConfig(
            max_rules=50,
            confidence_threshold=0.9,
            enable_auto_classify=False,
        )
        assert c.max_rules == 50
        assert c.confidence_threshold == 0.9
        assert c.enable_auto_classify is False

    def test_frozen(self) -> None:
        c = ClassifierConfig()
        with pytest.raises((ValueError, TypeError)):
            c.max_rules = 10  # type: ignore[misc]
