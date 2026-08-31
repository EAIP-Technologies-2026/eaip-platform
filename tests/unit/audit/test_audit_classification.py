"""Tests for DataClassifier."""

from __future__ import annotations

import pytest

from eaip.audit.classification import DataClassifier
from eaip.audit.exceptions import ClassificationError
from eaip.audit.models import ClassificationLevel, DataClassification


class TestDataClassifier:
    def test_classify_default_level(self) -> None:
        classifier = DataClassifier()
        result = classifier.classify({"type": "report"})
        assert result.level == ClassificationLevel.INTERNAL

    def test_classify_confidential_context(self) -> None:
        classifier = DataClassifier()
        result = classifier.classify({"type": "report"}, context={"confidential": True})
        assert result.level == ClassificationLevel.CONFIDENTIAL

    def test_classify_sensitive_context(self) -> None:
        classifier = DataClassifier()
        result = classifier.classify({"type": "pii"}, context={"sensitive": True})
        assert result.level == ClassificationLevel.RESTRICTED

    def test_classify_caches_result(self) -> None:
        classifier = DataClassifier()
        r1 = classifier.classify({"type": "report"})
        r2 = classifier.classify({"type": "report"})
        assert r1 is r2

    def test_classify_infers_data_type(self) -> None:
        classifier = DataClassifier()
        result = classifier.classify({"type": "custom_type"})
        assert result.id == "custom_type"

    async def test_evaluate_matching(self) -> None:
        classifier = DataClassifier()
        classification = DataClassification(
            id="report",
            name="Report",
            level=ClassificationLevel.INTERNAL,
        )
        classifier.register_classification(classification)
        result = await classifier.evaluate({"type": "report"}, classification)
        assert result is True

    async def test_evaluate_non_matching(self) -> None:
        classifier = DataClassifier()
        classification = DataClassification(
            id="report",
            name="Report",
            level=ClassificationLevel.RESTRICTED,
        )
        classifier.register_classification(classification)
        result = await classifier.evaluate({}, classification)
        assert result is False

    def test_get_classification_level(self) -> None:
        classifier = DataClassifier()
        classification = DataClassification(
            id="pii",
            name="PII",
            level=ClassificationLevel.RESTRICTED,
        )
        classifier.register_classification(classification)
        level = classifier.get_classification_level("pii")
        assert level == ClassificationLevel.RESTRICTED

    def test_get_classification_level_not_found(self) -> None:
        classifier = DataClassifier()
        with pytest.raises(ClassificationError):
            classifier.get_classification_level("unknown")

    def test_list_classifications(self) -> None:
        classifier = DataClassifier()
        assert classifier.list_classifications() == []
        classifier.register_classification(
            DataClassification(id="c1", name="C1", level=ClassificationLevel.PUBLIC),
        )
        classifier.register_classification(
            DataClassification(id="c2", name="C2", level=ClassificationLevel.INTERNAL),
        )
        assert len(classifier.list_classifications()) == 2

    def test_register_classification(self) -> None:
        classifier = DataClassifier()
        dc = DataClassification(id="dc1", name="Test", level=ClassificationLevel.CONFIDENTIAL)
        classifier.register_classification(dc)
        assert classifier.get_classification_level("dc1") == ClassificationLevel.CONFIDENTIAL
