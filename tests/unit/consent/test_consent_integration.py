from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.consent.integration import ConsentRuntimeModule


class TestConsentIntegration:
    def test_module_name(self) -> None:
        module = ConsentRuntimeModule()
        assert module.name == "consent"

    def test_health_check_property(self) -> None:
        module = ConsentRuntimeModule()
        check = module.health_check
        assert check.name == "consent"

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        module = ConsentRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()

        await module.start(kernel)
        kernel.platform.health.register.assert_called_once()

        await module.stop(kernel)

    def test_health_check_before_start(self) -> None:
        module = ConsentRuntimeModule()
        check = module.health_check
        assert check is not None
