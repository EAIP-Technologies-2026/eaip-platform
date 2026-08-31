"""Tests for MemoryRegistry."""

from __future__ import annotations

import pytest

from eaip.memory.models import MemoryItem, MemoryRelation, MemoryScope, MemoryType, ScopedMemoryId
from eaip.memory.registry import MemoryRegistry


@pytest.fixture
def scope() -> MemoryScope:
    return MemoryScope(tenant_id="t1", user_id="u1")


@pytest.fixture
def registry() -> MemoryRegistry:
    return MemoryRegistry()


@pytest.fixture
def item_a(scope: MemoryScope) -> MemoryItem:
    return MemoryItem(
        memory_id="a", memory_type=MemoryType.WORKING, scope=scope, content="alpha", tags=("x",)
    )


@pytest.fixture
def item_b(scope: MemoryScope) -> MemoryItem:
    return MemoryItem(
        memory_id="b", memory_type=MemoryType.WORKING, scope=scope, content="beta", tags=("y",)
    )


class TestMemoryRegistry:
    def test_register_and_get(
        self, registry: MemoryRegistry, scope: MemoryScope, item_a: MemoryItem
    ) -> None:
        registry.register(item_a)
        scoped_id = ScopedMemoryId(memory_id="a", scope=scope)
        result = registry.get(scoped_id)
        assert result is not None
        assert result.memory_id == "a"

    def test_get_nonexistent(self, registry: MemoryRegistry, scope: MemoryScope) -> None:
        scoped_id = ScopedMemoryId(memory_id="nonexistent", scope=scope)
        assert registry.get(scoped_id) is None

    def test_has(self, registry: MemoryRegistry, scope: MemoryScope, item_a: MemoryItem) -> None:
        registry.register(item_a)
        scoped_id = ScopedMemoryId(memory_id="a", scope=scope)
        assert registry.has(scoped_id) is True
        assert registry.has(ScopedMemoryId(memory_id="no", scope=scope)) is False

    def test_unregister(
        self, registry: MemoryRegistry, scope: MemoryScope, item_a: MemoryItem
    ) -> None:
        registry.register(item_a)
        scoped_id = ScopedMemoryId(memory_id="a", scope=scope)
        assert registry.unregister(scoped_id) is True
        assert registry.has(scoped_id) is False

    def test_unregister_nonexistent(self, registry: MemoryRegistry, scope: MemoryScope) -> None:
        scoped_id = ScopedMemoryId(memory_id="no", scope=scope)
        assert registry.unregister(scoped_id) is False

    def test_all(self, registry: MemoryRegistry, item_a: MemoryItem, item_b: MemoryItem) -> None:
        registry.register(item_a)
        registry.register(item_b)
        assert len(registry.all()) == 2

    def test_list_by_scope(
        self, registry: MemoryRegistry, scope: MemoryScope, item_a: MemoryItem
    ) -> None:
        other = MemoryScope(tenant_id="t2")
        registry.register(item_a)
        registry.register(
            MemoryItem(memory_id="c", memory_type=MemoryType.WORKING, scope=other, content="other")
        )
        items = registry.list_by_scope(scope)
        assert len(items) == 1

    def test_list_by_type(self, registry: MemoryRegistry, scope: MemoryScope) -> None:
        registry.register(
            MemoryItem(memory_id="w", memory_type=MemoryType.WORKING, scope=scope, content="x")
        )
        registry.register(
            MemoryItem(memory_id="s", memory_type=MemoryType.SESSION, scope=scope, content="y")
        )
        assert len(registry.list_by_type(MemoryType.WORKING)) == 1
        assert len(registry.list_by_type(MemoryType.SESSION)) == 1

    def test_list_by_tags(self, registry: MemoryRegistry, scope: MemoryScope) -> None:
        registry.register(
            MemoryItem(
                memory_id="a",
                memory_type=MemoryType.WORKING,
                scope=scope,
                content="x",
                tags=("important",),
            )
        )
        registry.register(
            MemoryItem(
                memory_id="b",
                memory_type=MemoryType.WORKING,
                scope=scope,
                content="y",
                tags=("normal",),
            )
        )
        items = registry.list_by_tags(("important",))
        assert len(items) == 1

    def test_count(self, registry: MemoryRegistry, scope: MemoryScope) -> None:
        registry.register(
            MemoryItem(memory_id="a", memory_type=MemoryType.WORKING, scope=scope, content="x")
        )
        assert registry.count() == 1

    def test_count_by_type(self, registry: MemoryRegistry, scope: MemoryScope) -> None:
        registry.register(
            MemoryItem(memory_id="a", memory_type=MemoryType.WORKING, scope=scope, content="x")
        )
        registry.register(
            MemoryItem(memory_id="b", memory_type=MemoryType.SESSION, scope=scope, content="y")
        )
        assert registry.count_by_type(MemoryType.WORKING) == 1
        assert registry.count_by_type(MemoryType.SESSION) == 1

    def test_count_by_scope(self, registry: MemoryRegistry, scope: MemoryScope) -> None:
        registry.register(
            MemoryItem(memory_id="a", memory_type=MemoryType.WORKING, scope=scope, content="x")
        )
        assert registry.count_by_scope(scope) == 1

    def test_relations(self, registry: MemoryRegistry) -> None:
        rel = MemoryRelation(source_id="a", target_id="b", relation_type="references")
        registry.add_relation(rel)
        relations = registry.get_relations("a")
        assert len(relations) == 1
        assert relations[0].relation_type == "references"

    def test_get_relations_by_type(self, registry: MemoryRegistry) -> None:
        r1 = MemoryRelation(source_id="a", target_id="b", relation_type="ref")
        r2 = MemoryRelation(source_id="a", target_id="c", relation_type="derives")
        registry.add_relation(r1)
        registry.add_relation(r2)
        assert len(registry.get_relations("a", relation_type="ref")) == 1
        assert len(registry.get_relations("a", relation_type="derives")) == 1

    def test_clear(self, registry: MemoryRegistry, scope: MemoryScope, item_a: MemoryItem) -> None:
        registry.register(item_a)
        rel = MemoryRelation(source_id="a", target_id="b", relation_type="ref")
        registry.add_relation(rel)
        registry.clear()
        assert registry.count() == 0
        assert len(registry.get_relations("a")) == 0

    @pytest.mark.asyncio
    async def test_health(
        self, registry: MemoryRegistry, scope: MemoryScope, item_a: MemoryItem
    ) -> None:
        registry.register(item_a)
        health = await registry.health()
        assert health["status"] == "healthy"
        assert health["items"] == 1
        assert health["relations"] == 0
