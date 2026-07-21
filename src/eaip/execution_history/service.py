"""Execution history service — CRUD, query, archive, export, analytics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from eaip.execution_history.exceptions import (
    ExecutionHistoryArchiveError,
    ExecutionHistoryExportError,
    ExecutionHistoryPurgeError,
    ExecutionHistoryQueryError,
    ExecutionRecordNotFoundError,
)
from eaip.execution_history.models import (
    ExecutionFilter,
    ExecutionHistoryConfig,
    ExecutionHistoryQuery,
    ExecutionHistoryResult,
    ExecutionHistoryStats,
    ExecutionRecord,
    ExecutionStatus,
)
from eaip.logging.context import get_logger


class ExecutionHistoryService:
    def __init__(
        self,
        config: ExecutionHistoryConfig | None = None,
    ) -> None:
        self._config = config or ExecutionHistoryConfig()
        self._records: dict[str, ExecutionRecord] = {}
        self._log = get_logger("eaip.execution_history.service")

    @property
    def config(self) -> ExecutionHistoryConfig:
        return self._config

    def create_record(
        self,
        workflow_id: str,
        workflow_name: str,
        *,
        trigger: str = "",
        input: dict[str, Any] | None = None,
        run_by: str = "",
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionRecord:
        now = datetime.utcnow()
        record = ExecutionRecord(
            id=str(uuid4()),
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            trigger=trigger,
            input=input or {},
            run_by=run_by,
            tags=tags,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        self._records[record.id] = record
        self._log.info("record.created", record_id=record.id, workflow_id=workflow_id)
        return record

    def get_record(self, record_id: str) -> ExecutionRecord:
        record = self._records.get(record_id)
        if record is None:
            raise ExecutionRecordNotFoundError(f"Execution record '{record_id}' not found")
        return record

    def update_record(
        self,
        record_id: str,
        *,
        status: ExecutionStatus | None = None,
        output: dict[str, Any] | None = None,
        error: str | None = None,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionRecord:
        existing = self.get_record(record_id)
        changes: dict[str, Any] = {}

        new_status = status if status is not None else existing.status
        new_output = output if output is not None else existing.output
        new_error = error if error is not None else existing.error
        new_duration = duration_ms if duration_ms is not None else existing.duration_ms
        new_metadata = metadata if metadata is not None else existing.metadata
        new_started_at = existing.started_at
        new_completed_at = existing.completed_at

        if status == ExecutionStatus.RUNNING and existing.started_at is None:
            new_started_at = datetime.utcnow()

        if status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
            new_completed_at = datetime.utcnow()

        if status != existing.status:
            changes["status"] = str(status)
        if new_duration != existing.duration_ms:
            changes["duration_ms"] = new_duration

        record = ExecutionRecord(
            id=existing.id,
            workflow_id=existing.workflow_id,
            workflow_name=existing.workflow_name,
            status=new_status,
            trigger=existing.trigger,
            input=existing.input,
            output=new_output,
            error=new_error,
            duration_ms=new_duration,
            started_at=new_started_at,
            completed_at=new_completed_at,
            created_at=existing.created_at,
            updated_at=datetime.utcnow(),
            run_by=existing.run_by,
            tags=existing.tags,
            metadata=new_metadata,
        )
        self._records[record_id] = record
        self._log.info("record.updated", record_id=record_id, changes=changes)
        return record

    def query(self, query: ExecutionHistoryQuery) -> ExecutionHistoryResult:
        try:
            matching = list(self._records.values())

            f = query.filter
            if f.workflow_ids:
                matching = [r for r in matching if r.workflow_id in f.workflow_ids]
            if f.statuses:
                matching = [r for r in matching if r.status in f.statuses]
            if f.run_by:
                matching = [r for r in matching if r.run_by == f.run_by]
            if f.trigger:
                matching = [r for r in matching if r.trigger == f.trigger]
            if f.date_from:
                matching = [r for r in matching if r.created_at >= f.date_from]
            if f.date_to:
                matching = [r for r in matching if r.created_at <= f.date_to]
            if f.tags:
                matching = [r for r in matching if any(t in r.tags for t in f.tags)]
            if f.search:
                search_lower = f.search.lower()
                matching = [
                    r
                    for r in matching
                    if search_lower in r.workflow_name.lower() or search_lower in r.id.lower()
                ]

            total = len(matching)

            if query.sort_desc:
                matching.sort(key=lambda r: getattr(r, query.sort_by, r.created_at), reverse=True)
            else:
                matching.sort(key=lambda r: getattr(r, query.sort_by, r.created_at))

            page = matching[query.offset : query.offset + query.limit]

            return ExecutionHistoryResult(
                records=tuple(page),
                total=total,
                offset=query.offset,
                limit=query.limit,
                has_more=(query.offset + query.limit) < total,
            )
        except Exception as exc:
            raise ExecutionHistoryQueryError(
                "Failed to query execution history",
                context={"offset": query.offset, "limit": query.limit},
                cause=exc,
            ) from exc

    def archive(self, older_than_days: int) -> int:
        try:
            cutoff = datetime.utcnow() - timedelta(days=older_than_days)
            to_archive = [rid for rid, rec in self._records.items() if rec.created_at < cutoff]
            for rid in to_archive:
                del self._records[rid]
            self._log.info(
                "records.archived", count=len(to_archive), older_than_days=older_than_days
            )
            return len(to_archive)
        except Exception as exc:
            raise ExecutionHistoryArchiveError(
                "Failed to archive execution history",
                context={"older_than_days": older_than_days},
                cause=exc,
            ) from exc

    def purge(self, older_than_days: int) -> int:
        try:
            cutoff = datetime.utcnow() - timedelta(days=older_than_days)
            to_purge = [rid for rid, rec in self._records.items() if rec.created_at < cutoff]
            for rid in to_purge:
                del self._records[rid]
            self._log.info("records.purged", count=len(to_purge), older_than_days=older_than_days)
            return len(to_purge)
        except Exception as exc:
            raise ExecutionHistoryPurgeError(
                "Failed to purge execution history",
                context={"older_than_days": older_than_days},
                cause=exc,
            ) from exc

    def export(
        self,
        format: str,
        destination: str,
        query: ExecutionHistoryQuery | None = None,
    ) -> int:
        try:
            if query is None:
                query = ExecutionHistoryQuery(
                    filter=ExecutionFilter(),
                    limit=self._config.export_max_records,
                )
            result = self.query(query)
            records = result.records

            self._log.info(
                "records.exported",
                count=len(records),
                format=format,
                destination=destination,
            )
            return len(records)
        except Exception as exc:
            raise ExecutionHistoryExportError(
                "Failed to export execution history",
                context={"format": format, "destination": destination},
                cause=exc,
            ) from exc

    def compute_analytics(self) -> ExecutionHistoryStats:
        total = len(self._records)
        completed = sum(1 for r in self._records.values() if r.status == ExecutionStatus.COMPLETED)
        failed = sum(1 for r in self._records.values() if r.status == ExecutionStatus.FAILED)
        running = sum(1 for r in self._records.values() if r.status == ExecutionStatus.RUNNING)
        pending = sum(1 for r in self._records.values() if r.status == ExecutionStatus.PENDING)
        cancelled = sum(1 for r in self._records.values() if r.status == ExecutionStatus.CANCELLED)
        skipped = sum(1 for r in self._records.values() if r.status == ExecutionStatus.SKIPPED)

        durations = [r.duration_ms for r in self._records.values() if r.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        sorted_durations = sorted(durations)
        p95 = sorted_durations[int(len(sorted_durations) * 0.95)] if sorted_durations else 0.0
        p99 = sorted_durations[int(len(sorted_durations) * 0.99)] if sorted_durations else 0.0

        return ExecutionHistoryStats(
            total_executions=total,
            completed=completed,
            failed=failed,
            running=running,
            pending=pending,
            cancelled=cancelled,
            skipped=skipped,
            avg_duration_ms=avg_duration,
            p95_duration_ms=p95,
            p99_duration_ms=p99,
        )

    def compact(self) -> int:
        now = datetime.utcnow()
        cutoff = now - timedelta(days=self._config.retention_days)
        to_remove = [
            rid
            for rid, rec in self._records.items()
            if rec.completed_at is not None and rec.completed_at < cutoff
        ]
        for rid in to_remove:
            del self._records[rid]
        self._log.info("records.compacted", count=len(to_remove))
        return len(to_remove)

    def get_events_for_record(self, record_id: str) -> list[dict[str, Any]]:
        self.get_record(record_id)
        return []

    def event_publisher(
        self,
    ) -> Any:
        return None


__all__ = ["ExecutionHistoryService"]
