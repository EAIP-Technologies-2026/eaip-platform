"""Change log service — record and query resource changes."""

from __future__ import annotations

from eaip.changelogsvc.models import ChangeEntry, ChangeLogConfig, ChangeQuery
from eaip.logging.context import get_logger


class ChangeLogService:
    """Service for recording and querying resource change history."""

    def __init__(self, config: ChangeLogConfig | None = None) -> None:
        self._config = config or ChangeLogConfig()
        self._entries: list[ChangeEntry] = []
        self._log = get_logger("eaip.changelogsvc.service")

    @property
    def config(self) -> ChangeLogConfig:
        return self._config

    async def record(self, entry: ChangeEntry) -> ChangeEntry:
        self._entries.append(entry)
        self._log.info("change.recorded", entry_id=entry.id, resource_id=entry.resource_id)
        return entry

    async def query(self, query: ChangeQuery) -> list[ChangeEntry]:
        results = self._entries
        if query.resource_id is not None:
            results = [e for e in results if e.resource_id == query.resource_id]
        if query.resource_type is not None:
            results = [e for e in results if e.resource_type == query.resource_type]
        if query.action is not None:
            results = [e for e in results if e.action == query.action]
        if query.changed_by is not None:
            results = [e for e in results if e.changed_by == query.changed_by]
        if query.from_time is not None:
            results = [e for e in results if e.changed_at >= query.from_time]
        if query.to_time is not None:
            results = [e for e in results if e.changed_at <= query.to_time]
        if query.correlation_id is not None:
            results = [e for e in results if e.correlation_id == query.correlation_id]
        return results[query.offset : query.offset + query.limit]

    async def count(self) -> int:
        return len(self._entries)
