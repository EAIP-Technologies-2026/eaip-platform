from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.filestore.asset_manager import AssetManager
from eaip.filestore.integration import FileStoreRuntimeModule


class TestFilestoreIntegration:
    def test_default_initialization(self) -> None:
        mod = FileStoreRuntimeModule()
        assert mod.name == "filestore"
        assert isinstance(mod.asset_manager, AssetManager)

    def test_custom_initialization(self) -> None:
        mgr = AssetManager()
        mod = FileStoreRuntimeModule(asset_manager=mgr)
        assert mod.asset_manager is mgr

    def test_startup_duration_default(self) -> None:
        mod = FileStoreRuntimeModule()
        assert mod.startup_duration == 0.0

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = FileStoreRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        assert mod.startup_duration > 0.0
        kernel.platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = FileStoreRuntimeModule()
        await mod.stop()
        # no exception is the assertion

    @pytest.mark.asyncio
    async def test_start_without_kernel(self) -> None:
        mod = FileStoreRuntimeModule()
        await mod.start()
        assert mod.startup_duration > 0.0

    @pytest.mark.asyncio
    async def test_health_check_registration(self) -> None:
        mod = FileStoreRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        await mod.start(kernel)
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert registered_check.name == "filestore"
