from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.compliance.framework import ComplianceFramework
from eaip.compliance.integration import ComplianceRuntimeModule


class TestComplianceIntegration:
    def test_default_initialization(self) -> None:
        mod = ComplianceRuntimeModule()
        assert mod.name == "compliance"
        assert isinstance(mod.framework, ComplianceFramework)

    def test_custom_initialization(self) -> None:
        fw = ComplianceFramework()
        mod = ComplianceRuntimeModule(framework=fw)
        assert mod.framework is fw

    def test_startup_duration_default(self) -> None:
        mod = ComplianceRuntimeModule()
        assert mod.startup_duration == 0.0

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = ComplianceRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        assert mod.startup_duration > 0.0
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = ComplianceRuntimeModule()
        await mod.stop()

    @pytest.mark.asyncio
    async def test_start_without_kernel(self) -> None:
        mod = ComplianceRuntimeModule()
        await mod.start()
        assert mod.startup_duration > 0.0

    @pytest.mark.asyncio
    async def test_health_check_registration(self) -> None:
        mod = ComplianceRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert registered_check.name == "compliance"
