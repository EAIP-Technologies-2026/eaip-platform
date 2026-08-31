from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.marketplace.integration import MarketplaceRuntimeModule
from eaip.marketplace.registry import MarketplaceRegistry


class TestMarketplaceIntegration:
    def test_default_initialization(self) -> None:
        mod = MarketplaceRuntimeModule()
        assert mod.name == "marketplace"
        assert isinstance(mod.registry, MarketplaceRegistry)

    def test_custom_initialization(self) -> None:
        reg = MarketplaceRegistry()
        from eaip.marketplace.models import MarketplacePackage, PackageType

        reg.register(
            MarketplacePackage(
                package_id="pkg-1",
                name="test",
                type=PackageType.AGENT,
                version="1.0.0",
                description="desc",
                author="dev",
            )
        )
        mod = MarketplaceRuntimeModule(registry=reg)
        assert mod.registry is reg

    def test_startup_duration_default(self) -> None:
        mod = MarketplaceRuntimeModule()
        assert mod.startup_duration == 0.0

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = MarketplaceRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        assert mod.startup_duration > 0.0
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = MarketplaceRuntimeModule()
        await mod.stop()

    @pytest.mark.asyncio
    async def test_start_without_kernel(self) -> None:
        mod = MarketplaceRuntimeModule()
        await mod.start()
        assert mod.startup_duration > 0.0

    @pytest.mark.asyncio
    async def test_health_check_registration(self) -> None:
        mod = MarketplaceRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert registered_check.name == "marketplace"
