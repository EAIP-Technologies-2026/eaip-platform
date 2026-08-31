from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.diagnostics.integration import DiagnosticsRuntimeModule


class TestDiagnosticsIntegration:
    def test_module_name(self) -> None:
        module = DiagnosticsRuntimeModule()
        assert module.name == "diagnostics"

    def test_health_check_property(self) -> None:
        module = DiagnosticsRuntimeModule()
        assert module.health_check.name == "diagnostics"

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        module = DiagnosticsRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()

        await module.start(kernel)
        kernel.platform.health.register.assert_called_once()

        await module.stop(kernel)
