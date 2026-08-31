"""Tests for ArchiveRuntimeModule."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.archive.integration import ArchiveRuntimeModule
from eaip.archive.manager import ArchiveManager
from eaip.archive.models import ArchiveConfig


class TestArchiveRuntimeModule:
    def test_default_name(self) -> None:
        mod = ArchiveRuntimeModule()
        assert mod.name == "archive"

    def test_default_manager(self) -> None:
        mod = ArchiveRuntimeModule()
        assert isinstance(mod.manager, ArchiveManager)

    def test_custom_config(self) -> None:
        config = ArchiveConfig(storage_backend="s3", retention_days=30)
        mod = ArchiveRuntimeModule(config=config)
        assert mod.manager.config.storage_backend == "s3"
        assert mod.manager.config.retention_days == 30

    def test_custom_manager(self) -> None:
        mgr = ArchiveManager()
        mod = ArchiveRuntimeModule(manager=mgr)
        assert mod.manager is mgr

    @pytest.mark.asyncio
    async def test_start_registers_capability_and_health(self) -> None:
        mod = ArchiveRuntimeModule()
        platform = MagicMock()
        platform.capabilities = MagicMock()
        platform.capabilities.register = MagicMock()
        platform.health = MagicMock()
        platform.health.register = MagicMock()
        kernel = AsyncMock()
        kernel.platform = platform

        await mod.start(kernel)

        platform.capabilities.register.assert_called_once()
        platform.health.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = ArchiveRuntimeModule()
        kernel = AsyncMock()
        await mod.stop(kernel)
