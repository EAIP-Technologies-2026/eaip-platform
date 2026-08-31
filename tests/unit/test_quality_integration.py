"""Tests for :mod:`eaip.quality.integration`."""

from __future__ import annotations

import pytest

from eaip.quality.coverage import CoverageAnalyzer
from eaip.quality.engine import TestEngine

TestEngine.__test__ = False
from eaip.quality.gates import QualityGateService
from eaip.quality.health import QualityHealthCheck
from eaip.quality.integration import QualityRuntimeModule
from eaip.quality.regression import RegressionDetector


class TestQualityRuntimeModule:
    def test_instantiation(self) -> None:
        module = QualityRuntimeModule()
        assert module.name == "quality"
        assert isinstance(module.engine, TestEngine)
        assert isinstance(module.gate_service, QualityGateService)
        assert isinstance(module.coverage_analyzer, CoverageAnalyzer)
        assert isinstance(module.regression_detector, RegressionDetector)
        assert isinstance(module.health_check, QualityHealthCheck)

    def test_all_services_independent(self) -> None:
        module = QualityRuntimeModule()
        assert module.engine is not module.gate_service
        assert module.coverage_analyzer is not module.regression_detector

    def test_health_check_references_services(self) -> None:
        module = QualityRuntimeModule()
        assert module.health_check._engine is module.engine
        assert module.health_check._gates is module.gate_service
        assert module.health_check._coverage is module.coverage_analyzer
        assert module.health_check._regression is module.regression_detector


class TestQualityHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        module = QualityRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "quality"
        assert report.status.value in ("healthy", "degraded")

    @pytest.mark.asyncio
    async def test_health_check_details(self) -> None:
        module = QualityRuntimeModule()
        report = await module.health_check.check()
        assert "test_case_count" in report.details
        assert "suite_count" in report.details
        assert "gate_count" in report.details

    @pytest.mark.asyncio
    async def test_health_check_with_tests(self) -> None:
        module = QualityRuntimeModule()
        from eaip.quality.models import TestCase

        module.engine.register_test_case(TestCase(id="tc1", name="test one"))
        report = await module.health_check.check()
        assert report.details["test_case_count"] >= 1
