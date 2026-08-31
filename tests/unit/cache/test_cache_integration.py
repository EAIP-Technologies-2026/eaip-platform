"""Tests for CacheRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from eaip.cache.integration import CacheRuntimeModule
from eaip.cache.manager import CacheManager
from eaip.cache.models import CacheConfig
from eaip.cache.provider import InMemoryCache


class TestCacheIntegration:
    def test_default_initialization(self) -> None:
        mod = CacheRuntimeModule()
        assert mod.name == "cache"

    def test_custom_initialization(self) -> None:
        cfg = CacheConfig(max_size_bytes=0, max_entries=500)
        mod = CacheRuntimeModule(config=cfg)
        assert mod.name == "cache"

    def test_create_manager(self) -> None:
        mod = CacheRuntimeModule()
        mgr = mod.create_manager()
        assert isinstance(mgr, CacheManager)

    def test_create_manager_with_config(self) -> None:
        cfg = CacheConfig(max_size_bytes=0, max_entries=500)
        mod = CacheRuntimeModule()
        mgr = mod.create_manager(config=cfg)
        assert isinstance(mgr, CacheManager)

    def test_create_in_memory_cache(self) -> None:
        mod = CacheRuntimeModule()
        cache = mod.create_in_memory_cache(max_entries=500, namespace="test")
        assert isinstance(cache, InMemoryCache)
        assert cache.namespace == "test"

    @pytest.mark.asyncio
    async def test_start_with_kernel(self) -> None:
        mod = CacheRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        kernel.platform.capabilities.register = MagicMock()
        await mod.start(kernel)
        kernel.platform.health.register.assert_called_once()
        kernel.platform.capabilities.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        mod = CacheRuntimeModule()
        kernel = MagicMock()
        await mod.start(kernel)
        await mod.stop(kernel)

    @pytest.mark.asyncio
    async def test_health_check_registration(self) -> None:
        mod = CacheRuntimeModule()
        kernel = MagicMock()
        kernel.platform.health.register = MagicMock()
        kernel.platform.capabilities.register = MagicMock()
        await mod.start(kernel)
        registered_check = kernel.platform.health.register.call_args[0][0]
        assert registered_check.name == "eaip.cache"
