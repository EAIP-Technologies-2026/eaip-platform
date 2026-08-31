"""ArchiveManager — create, restore, query, apply retention policies, and run cleanup cycles."""

from __future__ import annotations

import hashlib
import time
from datetime import timedelta
from typing import Any

from eaip.archive.exceptions import ArchiveNotFoundError
from eaip.archive.models import (
    ArchiveConfig,
    ArchiveQuery,
    ArchiveRecord,
    ArchiveResult,
    CleanupReport,
    RetentionPolicy,
)
from eaip.archive.store import ArchiveStore, LocalArchiveStore
from eaip.shared.time import utc_now


class ArchiveManager:
    """Manages archival operations: create, restore, query, retention, cleanup."""

    def __init__(
        self,
        config: ArchiveConfig | None = None,
        store: ArchiveStore | None = None,
    ) -> None:
        """Initialize the ArchiveManager with optional config and store."""
        self._config = config or ArchiveConfig()
        self._store = store or LocalArchiveStore(base_path="./archive")
        self._records: dict[str, ArchiveRecord] = {}
        self._policies: dict[str, RetentionPolicy] = {}

    @property
    def config(self) -> ArchiveConfig:
        """Return the archive configuration."""
        return self._config

    def create_archive(
        self,
        record_id: str,
        source_collection: str,
        data: bytes,
        *,
        checksum: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ArchiveRecord:
        """Create an archive record and store its data."""
        actual_checksum = checksum or hashlib.sha256(data).hexdigest()
        location = f"{source_collection}/{record_id}"
        record = ArchiveRecord(
            record_id=record_id,
            source_collection=source_collection,
            size_bytes=len(data),
            checksum=actual_checksum,
            location=location,
            metadata=metadata or {},
        )
        self._store.store(record_id, data)
        self._records[record_id] = record
        return record

    def restore(self, record_id: str) -> bytes:
        """Restore data for a given archive record."""
        record = self._records.get(record_id)
        if record is None:
            raise ArchiveNotFoundError(record_id)
        return self._store.retrieve(record_id)

    def query(self, query: ArchiveQuery) -> ArchiveResult:
        """Query archive records using the given query parameters."""
        matching = [r for r in self._records.values() if self._matches_query(r, query)]
        total = len(matching)
        page = query.offset // query.limit + 1 if query.limit else 1
        start = query.offset
        end = start + query.limit
        return ArchiveResult(
            records=tuple(matching[start:end]),
            total_count=total,
            page=page,
            page_size=query.limit,
        )

    def _matches_query(self, record: ArchiveRecord, query: ArchiveQuery) -> bool:
        for key, value in query.filters.items():
            if key == "source_collection" and record.source_collection != value:
                return False
            if key == "record_id" and record.record_id != value:
                return False
        if query.date_from is not None and record.archived_at < query.date_from:
            return False
        return not (query.date_to is not None and record.archived_at > query.date_to)

    def add_policy(self, policy: RetentionPolicy) -> None:
        """Register a retention policy."""
        self._policies[policy.policy_id] = policy

    def remove_policy(self, policy_id: str) -> None:
        """Remove a previously registered retention policy."""
        self._policies.pop(policy_id, None)

    def apply_retention_policy(self, policy_id: str) -> int:
        """Apply a retention policy and return the number of affected items."""
        policy = self._policies.get(policy_id)
        if policy is None:
            raise ArchiveNotFoundError(policy_id)
        now = utc_now()
        affected = 0
        to_remove: list[str] = []
        for rid, record in self._records.items():
            age = now - record.archived_at
            if policy.max_age_days > 0 and age > timedelta(days=policy.max_age_days):
                to_remove.append(rid)
                affected += 1
                continue
            if policy.max_size_bytes > 0 and record.size_bytes > policy.max_size_bytes:
                to_remove.append(rid)
                affected += 1
        for rid in to_remove:
            self._records.pop(rid, None)
        return affected

    def run_cleanup(self) -> CleanupReport:
        """Run a full cleanup cycle applying all registered retention policies."""
        start = time.monotonic()
        total_removed = 0
        total_bytes = 0
        policies_sorted = sorted(self._policies.values(), key=lambda p: p.priority, reverse=True)
        for policy in policies_sorted:
            removed = self.apply_retention_policy(policy.policy_id)
            total_removed += removed
        for record in self._records.values():
            total_bytes += record.size_bytes
        duration_ms = int((time.monotonic() - start) * 1000)
        return CleanupReport(
            items_removed=total_removed,
            bytes_freed=total_bytes,
            duration_ms=duration_ms,
        )


__all__ = ["ArchiveManager"]
