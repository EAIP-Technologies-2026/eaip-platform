"""Execution history - recording, querying, cleanup, and statistics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from eaip.automation.models import (
    AutomationExecution,
    AutomationStatus,
    ExecutionHistoryEntry,
    TriggerType,
)
from eaip.logging.context import get_logger


class ExecutionHistory:
    def __init__(self) -> None:
        self._log = get_logger("eaip.automation.history")
        self._entries: dict[str, ExecutionHistoryEntry] = {}
        self._details: dict[str, AutomationExecution] = {}

    async def record_execution(self, execution: AutomationExecution) -> None:
        entry = ExecutionHistoryEntry(
            execution_id=execution.id,
            rule_id=execution.rule_id,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration_ms=execution.duration_ms,
            trigger_type=execution.trigger_type,
            result_summary=execution.result,
            error_summary=execution.error,
        )
        self._entries[execution.id] = entry
        self._details[execution.id] = execution
        self._log.debug("history.recorded", execution_id=execution.id)

    async def get_history(
        self,
        rule_id: str | None = None,
        status: AutomationStatus | None = None,
        limit: int = 100,
    ) -> list[ExecutionHistoryEntry]:
        result = list(self._entries.values())
        if rule_id is not None:
            result = [e for e in result if e.rule_id == rule_id]
        if status is not None:
            result = [e for e in result if e.status == status]
        result.sort(key=lambda e: e.started_at, reverse=True)
        return result[:limit]

    async def get_execution_detail(self, execution_id: str) -> AutomationExecution | None:
        return self._details.get(execution_id)

    async def cleanup_history(self, retention_days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        before = len(self._entries)
        self._entries = {
            eid: entry
            for eid, entry in self._entries.items()
            if entry.started_at > cutoff
        }
        self._details = {
            eid: detail
            for eid, detail in self._details.items()
            if eid in self._entries
        }
        removed = before - len(self._entries)
        if removed:
            self._log.info("history.cleanup", removed=removed, retention_days=retention_days)
        return removed

    async def get_statistics(
        self, rule_id: str | None = None,
    ) -> dict[str, Any]:
        entries = list(self._entries.values())
        if rule_id is not None:
            entries = [e for e in entries if e.rule_id == rule_id]

        total = len(entries)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "skipped": 0,
                "pending": 0,
                "running": 0,
                "avg_duration_ms": 0.0,
                "success_rate": 0.0,
            }

        completed = sum(1 for e in entries if e.status == AutomationStatus.COMPLETED)
        failed = sum(1 for e in entries if e.status == AutomationStatus.FAILED)
        cancelled = sum(1 for e in entries if e.status == AutomationStatus.CANCELLED)
        skipped = sum(1 for e in entries if e.status == AutomationStatus.SKIPPED)
        pending = sum(1 for e in entries if e.status == AutomationStatus.PENDING)
        running = sum(1 for e in entries if e.status == AutomationStatus.RUNNING)
        avg_duration = sum(e.duration_ms for e in entries) / total if total > 0 else 0.0
        success_rate = (completed / total * 100) if total > 0 else 0.0

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "skipped": skipped,
            "pending": pending,
            "running": running,
            "avg_duration_ms": avg_duration,
            "success_rate": success_rate,
        }


__all__ = ["ExecutionHistory"]
