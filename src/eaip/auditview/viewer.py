"""AuditViewer — ingest, search, and export audit log entries."""

from __future__ import annotations

from typing import Any

from eaip.auditview.events import AuditExported, EntryIngested
from eaip.auditview.exceptions import EntryNotFoundError
from eaip.auditview.models import (
    AuditFilter,
    AuditLogEntry,
    AuditSearchResult,
    ViewerConfig,
)
from eaip.logging.context import get_logger


class AuditViewer:
    def __init__(self, config: ViewerConfig | None = None) -> None:
        self._config = config or ViewerConfig()
        self._entries: dict[str, AuditLogEntry] = {}
        self._log = get_logger("eaip.auditview.viewer")

    @property
    def config(self) -> ViewerConfig:
        return self._config

    async def ingest_entry(self, entry: AuditLogEntry) -> AuditLogEntry:
        self._entries[entry.id] = entry
        EntryIngested(
            entry_id=entry.id,
            actor=entry.actor,
            action=entry.action,
            resource=entry.resource,
        )
        self._log.info(
            "auditview.entry.ingested",
            entry_id=entry.id,
            actor=entry.actor,
            action=entry.action,
        )
        return entry

    async def search_entries(self, filter_: AuditFilter | None = None) -> AuditSearchResult:
        if filter_ is None:
            filter_ = AuditFilter()

        results: list[AuditLogEntry] = []
        for entry in self._entries.values():
            if filter_.actor is not None and entry.actor != filter_.actor:
                continue
            if filter_.action is not None and entry.action != filter_.action:
                continue
            if filter_.resource is not None and entry.resource != filter_.resource:
                continue
            if filter_.start_time is not None and entry.timestamp < filter_.start_time:
                continue
            if filter_.end_time is not None and entry.timestamp > filter_.end_time:
                continue
            if (
                filter_.correlation_id is not None
                and entry.correlation_id != filter_.correlation_id
            ):
                continue
            results.append(entry)

        total = len(results)
        paginated = results[filter_.offset : filter_.offset + filter_.limit]
        has_more = (filter_.offset + filter_.limit) < total

        return AuditSearchResult(
            total=total,
            entries=tuple(paginated),
            limit=filter_.limit,
            offset=filter_.offset,
            has_more=has_more,
        )

    async def get_entry(self, entry_id: str) -> AuditLogEntry:
        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFoundError(f"Audit entry '{entry_id}' not found")
        return entry

    async def get_actor_history(
        self,
        actor: str,
        limit: int = 50,
    ) -> list[AuditLogEntry]:
        results = [e for e in self._entries.values() if e.actor == actor]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def get_resource_timeline(
        self,
        resource: str,
        limit: int = 50,
    ) -> list[AuditLogEntry]:
        results = [e for e in self._entries.values() if e.resource == resource]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def export_entries(
        self,
        filter_: AuditFilter | None = None,
    ) -> list[dict[str, Any]]:
        result = await self.search_entries(filter_)
        export_limit = min(self._config.max_export_limit, result.total)
        entries_slice = list(result.entries)[:export_limit]
        AuditExported(
            filter_actor=filter_.actor if filter_ else None,
            filter_action=filter_.action if filter_ else None,
            filter_resource=filter_.resource if filter_ else None,
            entry_count=len(entries_slice),
        )
        self._log.info("auditview.export.completed", count=len(entries_slice))
        return [e.model_dump() for e in entries_slice]

    async def get_statistics(self) -> dict[str, Any]:
        total = len(self._entries)
        actors = len({e.actor for e in self._entries.values()})
        unique_actions = len({e.action for e in self._entries.values()})
        unique_resources = len({e.resource for e in self._entries.values()})
        return {
            "total_entries": total,
            "unique_actors": actors,
            "unique_actions": unique_actions,
            "unique_resources": unique_resources,
        }


__all__ = ["AuditViewer"]
