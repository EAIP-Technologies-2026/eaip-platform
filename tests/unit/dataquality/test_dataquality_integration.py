from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.dataquality.integration import DataQualityRuntimeModule
from eaip.dataquality.quality_service import DataQualityService
from eaip.dataquality.rule_engine import QualityRuleEngine


class TestDataqualityIntegration:
    def test_default_initialization(self) -> None:
        mod = DataQualityRuntimeModule()
        assert mod.name == "dataquality"
        assert isinstance(mod.rule_engine, QualityRuleEngine)
        assert isinstance(mod.quality_service, DataQualityService)

    def test_custom_initialization(self) -> None:
        re = QualityRuleEngine()
        qs = DataQualityService(rule_engine=re)
        mod = DataQualityRuntimeModule(rule_engine=re, quality_service=qs)
        assert mod.rule_engine is re
        assert mod.quality_service is qs

    def test_startup_duration_default(self) -> None:
        mod = DataQualityRuntimeModule()
        assert mod.startup_duration == 0.0

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = DataQualityRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        assert mod.startup_duration > 0.0
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = DataQualityRuntimeModule()
        await mod.stop()

    @pytest.mark.asyncio
    async def test_start_without_kernel(self) -> None:
        mod = DataQualityRuntimeModule()
        await mod.start()
        assert mod.startup_duration > 0.0

    @pytest.mark.asyncio
    async def test_health_check_registration(self) -> None:
        mod = DataQualityRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert registered_check.name == "dataquality"
