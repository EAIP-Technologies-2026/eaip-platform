"""Tests for :mod:`eaip.dataclassify.classifier`."""

from __future__ import annotations

import pytest

from eaip.dataclassify.classifier import DataClassifier
from eaip.dataclassify.models import DataCategory, DataClass


class TestDataClassifier:
    @pytest.fixture
    def classifier(self) -> DataClassifier:
        return DataClassifier()

    @pytest.fixture
    def ssn_rule(self) -> DataClass:
        return DataClass(
            id="r1",
            name="SSN",
            pattern="ssn",
            category=DataCategory.RESTRICTED,
            priority=10,
        )

    async def test_create_and_get_rule(self, classifier: DataClassifier) -> None:
        rule = DataClass(id="r1", name="Email", pattern="email", category=DataCategory.CONFIDENTIAL)
        created = await classifier.create_rule(rule)
        assert created.id == "r1"
        fetched = await classifier.get_rule("r1")
        assert fetched.name == "Email"

    async def test_get_rule_not_found(self, classifier: DataClassifier) -> None:
        with pytest.raises(Exception):
            await classifier.get_rule("nonexistent")

    async def test_update_rule(self, classifier: DataClassifier) -> None:
        rule = DataClass(id="r1", name="Original", pattern="p", category=DataCategory.PUBLIC)
        await classifier.create_rule(rule)
        updated = await classifier.update_rule("r1", name="Updated", priority=5)
        assert updated.name == "Updated"
        assert updated.priority == 5

    async def test_delete_rule(self, classifier: DataClassifier) -> None:
        rule = DataClass(id="r1", name="Del", pattern="p", category=DataCategory.PUBLIC)
        await classifier.create_rule(rule)
        await classifier.delete_rule("r1")
        with pytest.raises(Exception):
            await classifier.get_rule("r1")

    async def test_list_rules(self, classifier: DataClassifier) -> None:
        r1 = DataClass(id="r1", name="R1", pattern="p1", category=DataCategory.PUBLIC)
        r2 = DataClass(id="r2", name="R2", pattern="p2", category=DataCategory.CONFIDENTIAL)
        await classifier.create_rule(r1)
        await classifier.create_rule(r2)
        rules = await classifier.list_rules()
        assert len(rules) == 2

    async def test_classify(self, classifier: DataClassifier, ssn_rule: DataClass) -> None:
        await classifier.create_rule(ssn_rule)
        result = await classifier.classify("res-1", ("ssn", "pii"))
        assert "SSN" in result.detected_classes
        assert result.confidence > 0

    async def test_classify_no_match(self, classifier: DataClassifier) -> None:
        result = await classifier.classify("res-1", ("something",))
        assert result.detected_classes == ()
        assert result.confidence == 0.0
