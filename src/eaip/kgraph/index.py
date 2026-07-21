"""Graph index — inverted-index-based search for entities and relationships."""

from __future__ import annotations

from typing import Any

from eaip.kgraph.events import GraphIndexRebuilt
from eaip.kgraph.models import Entity, EntityIndex, Relationship
from eaip.logging.context import get_logger


class GraphIndex:
    """Inverted index for efficient entity and relationship search.

    Maintains per-field inverted indices that map values to lists of
    entity/relationship IDs, enabling fast lookup by type and property.
    """

    def __init__(self, graph: Any) -> None:
        self._graph = graph
        self._log = get_logger("eaip.kgraph.index")
        self._entity_indices: dict[str, EntityIndex] = {}
        self._relationship_type_index: dict[str, list[str]] = {}
        self._event_handlers: list[Any] = []

    def on(self, handler: Any) -> None:
        self._event_handlers.append(handler)

    async def _emit(self, event: Any) -> None:
        for handler in self._event_handlers:
            try:
                if callable(handler):
                    await handler(event)
            except Exception:
                self._log.warning("event.handler.failed", event_type=type(event).__name__)

    # ── indexing ─────────────────────────────────────────────────

    async def index_entity(self, entity: Entity) -> None:
        key = f"{entity.type}:type"
        if key not in self._entity_indices:
            self._entity_indices[key] = EntityIndex(
                entity_type=entity.type,
                field="type",
                values={entity.type: []},
            )
        if entity.id not in self._entity_indices[key].values.setdefault(entity.type, []):
            self._entity_indices[key].values[entity.type].append(entity.id)

        for field_name in ("name", "source"):
            value = getattr(entity, field_name, "")
            if value:
                fkey = f"{entity.type}:{field_name}"
                if fkey not in self._entity_indices:
                    self._entity_indices[fkey] = EntityIndex(
                        entity_type=entity.type,
                        field=field_name,
                        values={},
                    )
                idx = self._entity_indices[fkey].values.setdefault(str(value).lower(), [])
                if entity.id not in idx:
                    idx.append(entity.id)

        for prop_key, prop_value in entity.properties.items():
            if isinstance(prop_value, str) and prop_value:
                pkey = f"{entity.type}:prop:{prop_key}"
                if pkey not in self._entity_indices:
                    self._entity_indices[pkey] = EntityIndex(
                        entity_type=entity.type,
                        field=f"prop:{prop_key}",
                        values={},
                    )
                idx = self._entity_indices[pkey].values.setdefault(prop_value.lower(), [])
                if entity.id not in idx:
                    idx.append(entity.id)

        self._log.debug("entity.indexed", id=entity.id, type=entity.type)

    async def index_relationship(self, rel: Relationship) -> None:
        if rel.type not in self._relationship_type_index:
            self._relationship_type_index[rel.type] = []
        if rel.id not in self._relationship_type_index[rel.type]:
            self._relationship_type_index[rel.type].append(rel.id)
        self._log.debug("relationship.indexed", id=rel.id, type=rel.type)

    # ── search ───────────────────────────────────────────────────

    async def search_entities(
        self,
        query_str: str,
        entity_type: str | None = None,
    ) -> list[Entity]:
        q = query_str.lower()
        matched_ids: set[str] = set()

        for idx in self._entity_indices.values():
            if entity_type and entity_type != idx.entity_type:
                continue
            for index_value, eids in idx.values.items():
                if q in index_value.lower():
                    matched_ids.update(eids)

        return [self._graph.entities[eid] for eid in matched_ids if eid in self._graph.entities]

    async def search_relationships(self, rel_type: str | None = None) -> list[Relationship]:
        if rel_type:
            rel_ids = self._relationship_type_index.get(rel_type, [])
            return [
                self._graph.relationships[rid]
                for rid in rel_ids
                if rid in self._graph.relationships
            ]
        all_ids: list[str] = []
        for ids in self._relationship_type_index.values():
            all_ids.extend(ids)
        return [
            self._graph.relationships[rid] for rid in all_ids if rid in self._graph.relationships
        ]

    # ── index management ─────────────────────────────────────────

    async def rebuild_index(self) -> None:
        self._entity_indices.clear()
        self._relationship_type_index.clear()

        for entity in self._graph.entities.values():
            await self.index_entity(entity)
        for rel in self._graph.relationships.values():
            await self.index_relationship(rel)

        await self._emit(
            GraphIndexRebuilt(
                entity_count=len(self._graph.entities),
                relationship_count=len(self._graph.relationships),
            )
        )
        self._log.info(
            "index.rebuilt",
            entities=len(self._graph.entities),
            relationships=len(self._graph.relationships),
        )

    async def clear_index(self) -> None:
        self._entity_indices.clear()
        self._relationship_type_index.clear()
        self._log.info("index.cleared")

    # ── inspection ───────────────────────────────────────────────

    @property
    def entity_indices(self) -> dict[str, EntityIndex]:
        return dict(self._entity_indices)

    @property
    def relationship_type_index(self) -> dict[str, list[str]]:
        return dict(self._relationship_type_index)


__all__ = ["GraphIndex"]
