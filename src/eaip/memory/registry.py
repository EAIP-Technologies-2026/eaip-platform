"""MemoryRegistry — in-memory index and catalog for memory items."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.memory.models import MemoryItem, MemoryRelation, MemoryScope, MemoryType, ScopedMemoryId


class MemoryRegistry:
    """In-memory registry for tracking memory items and their relationships.

    Provides lightweight catalog functionality without requiring a full
    database query. Used by the MemoryEngine for fast lookups and
    relationship management.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._items: dict[str, MemoryItem] = {}
        self._relations: list[MemoryRelation] = []
        self._log = get_logger("eaip.memory.registry")

    def register(self, item: MemoryItem) -> None:
        """Register a memory item.

        Args:
            item: The memory item to register.
        """
        fq_id = ScopedMemoryId(memory_id=item.memory_id, scope=item.scope).fully_qualified()
        self._items[fq_id] = item
        self._log.debug("registry.register", fq_id=fq_id, memory_type=item.memory_type.value)

    def unregister(self, scoped_id: ScopedMemoryId) -> bool:
        """Unregister a memory item.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item was found and removed.
        """
        fq_id = scoped_id.fully_qualified()
        if fq_id in self._items:
            del self._items[fq_id]
            self._log.debug("registry.unregister", fq_id=fq_id)
            return True
        return False

    def get(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        """Get a registered memory item.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            The memory item, or None if not found.
        """
        return self._items.get(scoped_id.fully_qualified())

    def has(self, scoped_id: ScopedMemoryId) -> bool:
        """Check if a memory item is registered.

        Args:
            scoped_id: The scoped memory identifier.

        Returns:
            True if the item is registered.
        """
        return scoped_id.fully_qualified() in self._items

    def all(self) -> list[MemoryItem]:
        """Return all registered memory items.

        Returns:
            A list of all memory items.
        """
        return list(self._items.values())

    def list_by_scope(self, scope: MemoryScope) -> list[MemoryItem]:
        """List items within a given scope.

        Args:
            scope: The scope to filter by.

        Returns:
            A list of matching memory items.
        """
        scope_key = scope.scope_key()
        return [item for fq_id, item in self._items.items() if fq_id.startswith(scope_key)]

    def list_by_type(self, memory_type: MemoryType) -> list[MemoryItem]:
        """List items of a given memory type.

        Args:
            memory_type: The memory type to filter by.

        Returns:
            A list of matching memory items.
        """
        return [item for item in self._items.values() if item.memory_type == memory_type]

    def list_by_tags(self, tags: tuple[str, ...]) -> list[MemoryItem]:
        """List items with any of the given tags.

        Args:
            tags: The tags to match.

        Returns:
            A list of matching memory items.
        """
        return [item for item in self._items.values() if any(t in item.tags for t in tags)]

    def count(self) -> int:
        """Return the total number of registered items.

        Returns:
            The item count.
        """
        return len(self._items)

    def count_by_type(self, memory_type: MemoryType) -> int:
        """Count items of a given type.

        Args:
            memory_type: The memory type to count.

        Returns:
            The count of matching items.
        """
        return sum(1 for item in self._items.values() if item.memory_type == memory_type)

    def count_by_scope(self, scope: MemoryScope) -> int:
        """Count items within a scope.

        Args:
            scope: The scope to count within.

        Returns:
            The count of matching items.
        """
        return len(self.list_by_scope(scope))

    def add_relation(self, relation: MemoryRelation) -> None:
        """Register a relationship between two memory items.

        Args:
            relation: The relationship to register.
        """
        self._relations.append(relation)
        self._log.debug(
            "registry.add_relation",
            source=relation.source_id,
            target=relation.target_id,
            relation_type=relation.relation_type,
        )

    def get_relations(
        self,
        memory_id: str,
        relation_type: str | None = None,
    ) -> list[MemoryRelation]:
        """Get all relations for a memory item.

        Args:
            memory_id: The memory ID to find relations for.
            relation_type: Optional relation type filter.

        Returns:
            A list of matching relations.
        """
        results = [
            r
            for r in self._relations
            if memory_id in (r.source_id, r.target_id)
        ]
        if relation_type:
            results = [r for r in results if r.relation_type == relation_type]
        return results

    def clear(self) -> None:
        """Clear all registered items and relations."""
        count = len(self._items)
        self._items.clear()
        self._relations.clear()
        self._log.debug("registry.cleared", items_removed=count)

    async def health(self) -> dict[str, Any]:
        """Return health status for this registry.

        Returns:
            A dict with health information.
        """
        return {
            "status": "healthy",
            "items": self.count(),
            "relations": len(self._relations),
        }


__all__ = ["MemoryRegistry"]
