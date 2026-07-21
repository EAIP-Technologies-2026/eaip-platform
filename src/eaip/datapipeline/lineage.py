from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger


class DataLineageTracker:
    def __init__(self) -> None:
        self._log = get_logger("eaip.datapipeline.lineage")
        self._lineage: dict[str, list[dict[str, Any]]] = {}
        self._pipeline_lineage: dict[str, list[dict[str, Any]]] = {}

    async def record_lineage(
        self,
        execution_id: str,
        source: str,
        record_id: str,
        step_id: str,
        target: str,
    ) -> None:
        entry = {
            "execution_id": execution_id,
            "source": source,
            "record_id": record_id,
            "step_id": step_id,
            "target": target,
        }

        self._lineage.setdefault(record_id, []).append(entry)
        self._pipeline_lineage.setdefault(execution_id, []).append(entry)
        self._log.debug(
            "lineage.recorded",
            record_id=record_id,
            step_id=step_id,
            target=target,
        )

    async def get_lineage(self, record_id: str) -> list[dict[str, Any]]:
        return list(self._lineage.get(record_id, []))

    async def get_pipeline_lineage(self, pipeline_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for entries in self._pipeline_lineage.values():
            for entry in entries:
                result.append(entry)
        return [e for e in result if e.get("execution_id", "").startswith(pipeline_id)]

    async def trace_record(self, record_id: str) -> list[dict[str, Any]]:
        return await self.get_lineage(record_id)


__all__ = ["DataLineageTracker"]
