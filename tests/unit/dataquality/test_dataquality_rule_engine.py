from __future__ import annotations

import pytest

from eaip.dataquality.exceptions import (
    QualityCheckNotFoundError,
    QualityRuleNotFoundError,
)
from eaip.dataquality.models import (
    DataQualityConfig,
    QualityCheck,
    QualityResult,
    QualityRule,
    QualityViolation,
)
from eaip.dataquality.rule_engine import QualityRuleEngine


class TestDataqualityRuleEngine:
    def test_default_initialization(self) -> None:
        engine = QualityRuleEngine()
        assert isinstance(engine.config, DataQualityConfig)

    def test_custom_config(self) -> None:
        cfg = DataQualityConfig(default_severity="error")
        engine = QualityRuleEngine(config=cfg)
        assert engine.config.default_severity == "error"

    def test_create_rule(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="required_field", field="email", rule_type="required")
        result = engine.create_rule(rule)
        assert result is rule
        assert engine.get("r1") is rule

    def test_get_rule_none(self) -> None:
        engine = QualityRuleEngine()
        assert engine.get("missing") is None

    def test_get_rule_raises(self) -> None:
        engine = QualityRuleEngine()
        with pytest.raises(QualityRuleNotFoundError):
            engine.get_rule("missing")

    def test_update_rule(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="original", field="x", rule_type="required")
        engine.create_rule(rule)
        updated = engine.update_rule("r1", name="updated")
        assert updated.name == "updated"
        assert engine.get_rule("r1").name == "updated"

    def test_delete_rule(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="test", field="x", rule_type="required")
        engine.create_rule(rule)
        deleted = engine.delete_rule("r1")
        assert deleted is rule
        assert engine.get("r1") is None

    def test_delete_rule_not_found(self) -> None:
        engine = QualityRuleEngine()
        with pytest.raises(QualityRuleNotFoundError):
            engine.delete_rule("missing")

    def test_list_rules_empty(self) -> None:
        engine = QualityRuleEngine()
        assert engine.list_rules() == []

    def test_list_rules(self) -> None:
        engine = QualityRuleEngine()
        r1 = QualityRule(id="r1", name="a", field="x", rule_type="required")
        r2 = QualityRule(id="r2", name="b", field="y", rule_type="unique")
        engine.create_rule(r1)
        engine.create_rule(r2)
        rules = engine.list_rules()
        assert len(rules) == 2
        assert r1 in rules
        assert r2 in rules

    def test_create_check(self) -> None:
        engine = QualityRuleEngine()
        check = QualityCheck(id="c1", name="daily")
        result = engine.create_check(check)
        assert result is check

    def test_get_check(self) -> None:
        engine = QualityRuleEngine()
        check = QualityCheck(id="c1", name="daily")
        engine.create_check(check)
        assert engine.get_check("c1") is check

    def test_get_check_not_found(self) -> None:
        engine = QualityRuleEngine()
        with pytest.raises(QualityCheckNotFoundError):
            engine.get_check("missing")

    def test_list_checks(self) -> None:
        engine = QualityRuleEngine()
        c1 = QualityCheck(id="c1", name="a")
        c2 = QualityCheck(id="c2", name="b")
        engine.create_check(c1)
        engine.create_check(c2)
        assert len(engine.list_checks()) == 2

    @pytest.mark.asyncio
    async def test_validate_required_passes(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required")
        passed, violations = await engine.validate(rule, {"name": "Alice"})
        assert passed is True
        assert violations == []

    @pytest.mark.asyncio
    async def test_validate_required_fails_empty(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required")
        passed, violations = await engine.validate(rule, {"name": ""})
        assert passed is False
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_validate_required_fails_none(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required")
        passed, violations = await engine.validate(rule, {"name": None})
        assert passed is False
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_validate_disabled_rule(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required", enabled=False)
        passed, violations = await engine.validate(rule, {"name": None})
        assert passed is True
        assert violations == []

    @pytest.mark.asyncio
    async def test_validate_range_min(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(
            id="r1",
            name="range",
            field="age",
            rule_type="range",
            params={"min": 0, "max": 150},
        )
        passed, _violations = await engine.validate(rule, {"age": -1})
        assert passed is False

    @pytest.mark.asyncio
    async def test_validate_range_max(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(
            id="r1",
            name="range",
            field="age",
            rule_type="range",
            params={"min": 0, "max": 150},
        )
        passed, _violations = await engine.validate(rule, {"age": 200})
        assert passed is False

    @pytest.mark.asyncio
    async def test_validate_range_passes(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(
            id="r1",
            name="range",
            field="age",
            rule_type="range",
            params={"min": 0, "max": 150},
        )
        passed, _violations = await engine.validate(rule, {"age": 25})
        assert passed is True

    @pytest.mark.asyncio
    async def test_validate_pattern(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(
            id="r1",
            name="email",
            field="email",
            rule_type="pattern",
            params={"pattern": r".+@.+\..+"},
        )
        passed, _violations = await engine.validate(rule, {"email": "bad"})
        assert passed is False

    @pytest.mark.asyncio
    async def test_validate_pattern_passes(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(
            id="r1",
            name="email",
            field="email",
            rule_type="pattern",
            params={"pattern": r".+@.+\..+"},
        )
        passed, _violations = await engine.validate(rule, {"email": "a@b.com"})
        assert passed is True

    @pytest.mark.asyncio
    async def test_validate_type(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(
            id="r1", name="type_int", field="age", rule_type="type", params={"type": "int"}
        )
        passed, _violations = await engine.validate(rule, {"age": "not_int"})
        assert passed is False

    @pytest.mark.asyncio
    async def test_validate_type_passes(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(
            id="r1", name="type_int", field="age", rule_type="type", params={"type": "int"}
        )
        passed, _violations = await engine.validate(rule, {"age": 30})
        assert passed is True

    @pytest.mark.asyncio
    async def test_validate_custom_passes(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="custom", field="x", rule_type="custom")
        passed, _violations = await engine.validate(rule, {"x": "anything"})
        assert passed is True

    @pytest.mark.asyncio
    async def test_validate_all(self) -> None:
        engine = QualityRuleEngine()
        r1 = QualityRule(id="r1", name="req", field="name", rule_type="required")
        r2 = QualityRule(id="r2", name="range", field="age", rule_type="range", params={"min": 0})
        results = await engine.validate_all([r1, r2], {"name": "Alice", "age": -1})
        assert len(results) == 2
        assert results[0][0] is True
        assert results[1][0] is False

    @pytest.mark.asyncio
    async def test_execute_check(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required")
        engine.create_rule(rule)
        check = QualityCheck(id="c1", name="test", rules=("r1",))
        engine.create_check(check)
        result = await engine.execute_check("c1")
        assert isinstance(result, QualityResult)
        assert result.check_id == "c1"

    @pytest.mark.asyncio
    async def test_execute_all_checks(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required")
        engine.create_rule(rule)
        check = QualityCheck(id="c1", name="test", rules=("r1",))
        engine.create_check(check)
        results = await engine.execute_all_checks()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_violations(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required")
        await engine.validate(rule, {"name": ""})
        await engine.validate(rule, {"name": None})
        violations = await engine.get_violations("r1")
        assert len(violations) == 2

    @pytest.mark.asyncio
    async def test_get_violations_limit(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required")
        for _ in range(5):
            await engine.validate(rule, {"name": ""})
        violations = await engine.get_violations("r1", limit=3)
        assert len(violations) == 3

    @pytest.mark.asyncio
    async def test_violation_details(self) -> None:
        engine = QualityRuleEngine()
        rule = QualityRule(
            id="r1", name="req", field="email", rule_type="required", severity="warning"
        )
        passed, violations = await engine.validate(rule, {"id": "rec1", "email": None})
        assert passed is False
        v = violations[0]
        assert isinstance(v, QualityViolation)
        assert v.rule_id == "r1"
        assert v.field == "email"
        assert v.severity == "warning"
        assert v.record_id == "rec1"
