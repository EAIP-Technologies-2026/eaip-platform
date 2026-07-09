"""Tests for MemoryIntegration and MemoryRuntimeModule."""

from __future__ import annotations

import pytest

from eaip.memory.integration import MemoryIntegration, MemoryRuntimeModule, create_memory_integration
from eaip.memory.models import MemoryConfig, RetentionConfig
from eaip.memory.store import InMemoryStore


class TestMemoryIntegration:
    @pytest.mark.asyncio
    async def test_start_creates_default_engine(self) -> None:
        integration = MemoryIntegration()
        assert integration.startup_duration == 0.0
        await integration.start()
        assert integration.engine is not None
        assert integration.startup_duration > 0

    @pytest.mark.asyncio
    async def test_start_with_existing_engine(self) -> None:
        store = InMemoryStore()
        from eaip.memory.engine import MemoryEngine
        engine = MemoryEngine(store)
        integration = MemoryIntegration(engine=engine)
        await integration.start()
        assert integration.engine is engine

    @pytest.mark.asyncio
    async def test_engine_property_before_start_raises(self) -> None:
        integration = MemoryIntegration()
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = integration.engine

    @pytest.mark.asyncio
    async def test_stop(self) -> None:
        integration = MemoryIntegration()
        await integration.start()
        await integration.stop()

    def test_on_event(self) -> None:
        integration = MemoryIntegration()
        integration.on_event(lambda e: None)

    def test_name(self) -> None:
        assert MemoryIntegration.name == "memory"


class TestCreateMemoryIntegration:
    def test_create_with_defaults(self) -> None:
        integration = create_memory_integration()
        assert integration is not None

    def test_create_with_store(self) -> None:
        store = InMemoryStore()
        integration = create_memory_integration(store)
        assert integration is not None

    def test_create_with_config(self) -> None:
        config = MemoryConfig(default_importance=0.9)
        retention = RetentionConfig(working_ttl_seconds=100)
        integration = create_memory_integration(config=config, retention=retention)
        assert integration is not None


class TestMemoryRuntimeModule:
    def test_is_subclass(self) -> None:
        assert issubclass(MemoryRuntimeModule, MemoryIntegration)

    @pytest.mark.asyncio
    async def test_runtime_module_lifecycle(self) -> None:
        module = MemoryRuntimeModule()
        await module.start()
        assert module.engine is not None
        await module.stop()
