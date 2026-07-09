"""Tests for memory consolidation strategies and service."""

from __future__ import annotations

import pytest

from eaip.memory.consolidation import (
    ConditionalConsolidationStrategy,
    MemoryConsolidationService,
    NeverConsolidateStrategy,
    TimeBasedConsolidationStrategy,
)
from eaip.memory.models import ConsolidationConfig, ConsolidationReport, MemoryItem, MemoryScope, MemoryType


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(tenant_id="t1")


@pytest.fixture
def config() -> ConsolidationConfig:
    return ConsolidationConfig(min_memories_for_consolidation=3)


@pytest.fixture
def memories(scope: MemoryScope) -> list[MemoryItem]:
    return [
        MemoryItem(memory_id=f"m{i}", memory_type=MemoryType.EPISODIC, scope=scope, content=f"event {i}")
        for i in range(5)
    ]


class TestTimeBasedConsolidationStrategy:
    @pytest.mark.asyncio
    async def test_should_consolidate_enough_memories(self, config: ConsolidationConfig, memories: list[MemoryItem]) -> None:
        strategy = TimeBasedConsolidationStrategy()
        result = await strategy.should_consolidate(memories, config)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_not_consolidate_few_memories(self, config: ConsolidationConfig, scope: MemoryScope) -> None:
        strategy = TimeBasedConsolidationStrategy()
        few = [MemoryItem(memory_id="m1", memory_type=MemoryType.EPISODIC, scope=scope, content="x")]
        result = await strategy.should_consolidate(few, config)
        assert result is False

    @pytest.mark.asyncio
    async def test_consolidate(self, config: ConsolidationConfig, memories: list[MemoryItem]) -> None:
        strategy = TimeBasedConsolidationStrategy()
        report = await strategy.consolidate(memories, config)
        assert report.source_count == 5
        assert report.details.get("ready") is True


class TestNeverConsolidateStrategy:
    @pytest.mark.asyncio
    async def test_never_consolidates(self, config: ConsolidationConfig, memories: list[MemoryItem]) -> None:
        strategy = NeverConsolidateStrategy()
        assert await strategy.should_consolidate(memories, config) is False

    @pytest.mark.asyncio
    async def test_consolidate_returns_empty(self, config: ConsolidationConfig, memories: list[MemoryItem]) -> None:
        strategy = NeverConsolidateStrategy()
        report = await strategy.consolidate(memories, config)
        assert report.source_count == 0


class TestConditionalConsolidationStrategy:
    @pytest.mark.asyncio
    async def test_default_condition(self, config: ConsolidationConfig, memories: list[MemoryItem]) -> None:
        strategy = ConditionalConsolidationStrategy()
        result = await strategy.should_consolidate(memories, config)
        assert result is True

    @pytest.mark.asyncio
    async def test_custom_condition(self, config: ConsolidationConfig, memories: list[MemoryItem]) -> None:
        def condition(_mems: list[MemoryItem], _cfg: ConsolidationConfig) -> bool:
            return False

        strategy = ConditionalConsolidationStrategy(condition=condition)
        result = await strategy.should_consolidate(memories, config)
        assert result is False

    @pytest.mark.asyncio
    async def test_custom_action(self, config: ConsolidationConfig, memories: list[MemoryItem]) -> None:
        def action(_mems: list[MemoryItem], _cfg: ConsolidationConfig) -> ConsolidationReport:
            return ConsolidationReport(source_count=len(_mems), consolidated_count=2)

        strategy = ConditionalConsolidationStrategy(action=action)
        report = await strategy.consolidate(memories, config)
        assert report.source_count == 5
        assert report.consolidated_count == 2


class TestMemoryConsolidationService:
    @pytest.mark.asyncio
    async def test_consolidate_episodic_to_semantic(self, config: ConsolidationConfig, scope: MemoryScope) -> None:
        service = MemoryConsolidationService(config=config)
        memories = [
            MemoryItem(memory_id=f"m{i}", memory_type=MemoryType.EPISODIC, scope=scope, content=f"event {i}", tags=("tag",))
            for i in range(5)
        ]
        report = await service.consolidate_episodic_to_semantic(memories)
        assert report.source_count == 5
        assert report.consolidated_count == 1
        assert report.summaries_generated == 1
        assert report.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_consolidate_empty_list(self, config: ConsolidationConfig) -> None:
        service = MemoryConsolidationService(config=config)
        report = await service.consolidate_episodic_to_semantic([])
        assert report.source_count == 0

    @pytest.mark.asyncio
    async def test_consolidate_not_enough(self, scope: MemoryScope) -> None:
        config = ConsolidationConfig(min_memories_for_consolidation=10)
        service = MemoryConsolidationService(config=config)
        memories = [
            MemoryItem(memory_id="m1", memory_type=MemoryType.EPISODIC, scope=scope, content="x"),
        ]
        report = await service.consolidate_episodic_to_semantic(memories)
        assert report.source_count == 1
        assert report.consolidated_count == 0

    @pytest.mark.asyncio
    async def test_deduplicate(self, scope: MemoryScope) -> None:
        service = MemoryConsolidationService()
        memories = [
            MemoryItem(memory_id="m1", memory_type=MemoryType.EPISODIC, scope=scope, content="same"),
            MemoryItem(memory_id="m2", memory_type=MemoryType.EPISODIC, scope=scope, content="same"),
            MemoryItem(memory_id="m3", memory_type=MemoryType.EPISODIC, scope=scope, content="different"),
        ]
        unique, duplicates = await service.deduplicate(memories)
        assert len(unique) == 2
        assert len(duplicates) == 1

    @pytest.mark.asyncio
    async def test_deduplicate_no_duplicates(self, scope: MemoryScope) -> None:
        service = MemoryConsolidationService()
        memories = [
            MemoryItem(memory_id="m1", memory_type=MemoryType.EPISODIC, scope=scope, content="a"),
            MemoryItem(memory_id="m2", memory_type=MemoryType.EPISODIC, scope=scope, content="b"),
        ]
        unique, duplicates = await service.deduplicate(memories)
        assert len(unique) == 2
        assert len(duplicates) == 0
