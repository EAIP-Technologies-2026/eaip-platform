"""Snapshot service — create, retrieve, and manage aggregate snapshots."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.eventsourcing.exceptions import SnapshotNotFoundError
from eaip.eventsourcing.store import EventStore
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class SnapshotEntry:
    def __init__(
        self,
        aggregate_type: str,
        aggregate_id: str,
        state: dict[str, Any],
        version: int = 0,
        created_at: datetime | None = None,
    ) -> None:
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.state = state
        self.version = version
        self.created_at = created_at or utc_now()


class SnapshotService:
    def __init__(self, store: EventStore, snapshot_frequency: int = 100) -> None:
        self._store = store
        self._snapshot_frequency = snapshot_frequency
        self._snapshots: dict[str, SnapshotEntry] = {}
        self._log = get_logger("eaip.eventsourcing.snapshots")

    async def create_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: str,
        state: dict[str, Any],
    ) -> SnapshotEntry:
        events = self._store.get_events(aggregate_type, aggregate_id)
        version = len(events)
        key = self._key(aggregate_type, aggregate_id)
        entry = SnapshotEntry(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            state=state,
            version=version,
        )
        self._snapshots[key] = entry
        self._log.debug(
            "snapshot.created",
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            version=version,
        )
        return entry

    async def get_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> SnapshotEntry:
        key = self._key(aggregate_type, aggregate_id)
        entry = self._snapshots.get(key)
        if entry is None:
            raise SnapshotNotFoundError(f"No snapshot found for {aggregate_type}:{aggregate_id}")
        return entry

    async def delete_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> None:
        key = self._key(aggregate_type, aggregate_id)
        if key not in self._snapshots:
            raise SnapshotNotFoundError(f"No snapshot found for {aggregate_type}:{aggregate_id}")
        del self._snapshots[key]
        self._log.debug(
            "snapshot.deleted", aggregate_type=aggregate_type, aggregate_id=aggregate_id
        )

    async def should_create_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> bool:
        key = self._key(aggregate_type, aggregate_id)
        events = self._store.get_events(aggregate_type, aggregate_id)
        current_version = len(events)

        existing = self._snapshots.get(key)
        if existing is None:
            return current_version >= self._snapshot_frequency

        return (current_version - existing.version) >= self._snapshot_frequency

    @staticmethod
    def _key(aggregate_type: str, aggregate_id: str) -> str:
        return f"{aggregate_type}:{aggregate_id}"


__all__ = ["SnapshotEntry", "SnapshotService"]
