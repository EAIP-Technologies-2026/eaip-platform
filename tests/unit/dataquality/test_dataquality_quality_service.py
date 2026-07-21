from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.dataquality.models import DataQualityConfig, QualityResult, QualityRule
from eaip.dataquality.quality_service import DataQualityService
from eaip.dataquality.rule_engine import QualityRuleEngine


class TestDataqualityQualityService:
    def test_default_initialization(self) -> None:
        re = QualityRuleEngine()
        svc = DataQualityService(rule_engine=re)
        assert svc.rule_engine is re
        assert isinstance(svc.rule_engine, QualityRuleEngine)

    def test_custom_initialization(self) -> None:
        re = QualityRuleEngine()
        cfg = DataQualityConfig(default_severity="error")
        svc = DataQualityService(rule_engine=re, config=cfg)
        assert svc.rule_engine is re

    @pytest.mark.asyncio
    async def test_run_quality_check_passed(self) -> None:
        re = QualityRuleEngine()
        rule = QualityRule(id="r1", name="req", field="name", rule_type="required")
        re.create_rule(rule)
        svc = DataQualityService(rule_engine=re)
        data = [{"name": "Alice"}, {"name": "Bob"}]
        result = await svc.run_quality_check(data, [rule])
        assert isinstance(result, QualityResult)
        assert result.status == "passed"
        assert result.total_checks > 0

    @pytest.mark.asyncio
    async def test_run_quality_check_failed(self) -> None:
        re = QualityRuleEngine()
        rule = QualityRule(id="r2", name="req", field="name", rule_type="required")
        re.create_rule(rule)
        svc = DataQualityService(rule_engine=re)
        data = [{"name": ""}, {"name": None}]
        result = await svc.run_quality_check(data, [rule])
        assert result.status == "failed"
        assert result.failed_checks > 0

    @pytest.mark.asyncio
    async def test_profile_data(self) -> None:
        re = QualityRuleEngine()
        svc = DataQualityService(rule_engine=re)
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}, {"name": None, "age": 35}]
        profile = await svc.profile_data(data)
        assert profile["record_count"] == 3
        assert "name" in profile["fields"]
        assert "age" in profile["fields"]
        assert profile["fields"]["age"]["mean"] == 30.0

    @pytest.mark.asyncio
    async def test_profile_data_empty(self) -> None:
        re = QualityRuleEngine()
        svc = DataQualityService(rule_engine=re)
        profile = await svc.profile_data([])
        assert profile["record_count"] == 0
        assert profile["fields"] == {}

    @pytest.mark.asyncio
    async def test_detect_anomalies(self) -> None:
        re = QualityRuleEngine()
        svc = DataQualityService(rule_engine=re)
        data = [{"value": 1}] * 10 + [{"value": 1000}]
        anomalies = await svc.detect_anomalies(data, "value")
        assert len(anomalies) == 1
        assert anomalies[0]["value"] == 1000
        assert anomalies[0]["severity"] == "error"

    @pytest.mark.asyncio
    async def test_detect_anomalies_insufficient_data(self) -> None:
        re = QualityRuleEngine()
        svc = DataQualityService(rule_engine=re)
        anomalies = await svc.detect_anomalies([{"value": 1}, {"value": 2}], "value")
        assert anomalies == []

    @pytest.mark.asyncio
    async def test_detect_anomalies_zero_stdev(self) -> None:
        re = QualityRuleEngine()
        svc = DataQualityService(rule_engine=re)
        data = [{"value": 5}, {"value": 5}, {"value": 5}]
        anomalies = await svc.detect_anomalies(data, "value")
        assert anomalies == []

    @pytest.mark.asyncio
    async def test_get_data_profile(self) -> None:
        re = QualityRuleEngine()
        svc = DataQualityService(rule_engine=re)
        data = [{"x": 1}]
        profile = await svc.get_data_profile(data)
        assert profile["record_count"] == 1

    @pytest.mark.asyncio
    async def test_run_quality_check_handles_errors(self) -> None:
        re = MagicMock(spec=QualityRuleEngine)
        re.validate = AsyncMock(side_effect=ValueError("oops"))
        svc = DataQualityService(rule_engine=re)
        rule = QualityRule(id="r1", name="test", field="x", rule_type="required")
        data = [{"x": 1}]
        result = await svc.run_quality_check(data, [rule])
        assert result.status == "error"
        assert "oops" in result.errors
