"""Tests for MemoryHealthCheck."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.memory.engine import MemoryEngine
from eaip.memory.health import MemoryHealthCheck
from eaip.memory.models import MemoryItem, MemoryScope, MemoryType
from eaip.memory.registry import MemoryRegistry
from eaip.memory.store import InMemoryStore


class TestMemoryHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_with_registry(self) -> None:
        registry = MemoryRegistry()
        health = MemoryHealthCheck(registry)
        report = await health.check()
        assert report.component == "memory"
        assert report.status is HealthStatus.HEALTHY
        assert report.details.get("items") == 0

    @pytest.mark.asyncio
    async def test_health_check_with_registry_with_items(self) -> None:
        registry = MemoryRegistry()
        scope = MemoryScope(tenant_id="t1")
        item = MemoryItem(memory_id="m1", memory_type=MemoryType.WORKING, scope=scope, content="x")
        registry.register(item)
        health = MemoryHealthCheck(registry)
        report = await health.check()
        assert report.details.get("items") == 1

    @pytest.mark.asyncio
    async def test_health_check_with_engine(self) -> None:
        store = InMemoryStore()
        engine = MemoryEngine(store)
        health = MemoryHealthCheck(engine)
        report = await health.check()
        assert report.status is HealthStatus.HEALTHY
        assert "engine" in report.details

    @pytest.mark.asyncio
    async def test_health_check_name(self) -> None:
        registry = MemoryRegistry()
        health = MemoryHealthCheck(registry)
        assert health.name == "memory"
