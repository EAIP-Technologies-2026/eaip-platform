"""KPI measurement tracker — records, trends, and status checks for KPIs."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from eaip.goals.exceptions import KpiNotFoundError
from eaip.goals.models import KpiDirection, KpiDefinition
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class _KpiRecord:
    """A single recorded KPI measurement."""

    __slots__ = ("value", "timestamp")

    def __init__(self, value: float, timestamp: datetime | None = None) -> None:
        self.value = value
        self.timestamp = timestamp or utc_now()


class GoalTracker:
    """Records KPI measurements and provides trend analysis."""

    def __init__(self) -> None:
        self._history: dict[str, list[_KpiRecord]] = defaultdict(list)
        self._kpis: dict[str, KpiDefinition] = {}
        self._log = get_logger("eaip.goals.tracker")

    def register_kpi(self, kpi: KpiDefinition) -> None:
        """Register a KPI definition for tracking."""
        self._kpis[kpi.id] = kpi

    async def record_kpi(self, kpi_id: str, value: float, timestamp: datetime | None = None) -> float:
        """Record a KPI measurement and return the previous value."""
        if kpi_id not in self._kpis:
            raise KpiNotFoundError(kpi_id)

        previous = self._kpis[kpi_id].current_value
        self._history[kpi_id].append(_KpiRecord(value, timestamp))
        # Update the current value on the definition (via object creation trick)
        old = self._kpis[kpi_id]
        self._kpis[kpi_id] = KpiDefinition(
            id=old.id,
            name=old.name,
            description=old.description,
            unit=old.unit,
            target_value=old.target_value,
            current_value=value,
            measurement_type=old.measurement_type,
            direction=old.direction,
            met_threshold=old.met_threshold,
        )
        self._log.info("kpi.recorded", kpi_id=kpi_id, value=value)
        return previous

    async def get_kpi_history(self, kpi_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get the measurement history for a KPI."""
        if kpi_id not in self._kpis:
            raise KpiNotFoundError(kpi_id)

        records = self._history.get(kpi_id, [])
        return [
            {"value": r.value, "timestamp": r.timestamp}
            for r in records[-limit:]
        ]

    async def calculate_kpi_trend(self, kpi_id: str) -> str:
        """Calculate the trend direction for a KPI."""
        if kpi_id not in self._kpis:
            raise KpiNotFoundError(kpi_id)

        records = self._history.get(kpi_id, [])
        if len(records) < 2:
            return "stable"

        recent = records[-5:] if len(records) >= 5 else records
        first_val = recent[0].value
        last_val = recent[-1].value
        diff = last_val - first_val
        tolerance = 0.01 * max(abs(first_val), abs(last_val), 1.0)

        if abs(diff) <= tolerance:
            return "stable"
        return "increasing" if diff > 0 else "decreasing"

    async def check_kpi_status(self, kpi_id: str) -> dict[str, Any]:
        """Check if a KPI is on track to meet its target."""
        if kpi_id not in self._kpis:
            raise KpiNotFoundError(kpi_id)

        kpi = self._kpis[kpi_id]
        if kpi.target_value == 0:
            return {"on_track": True, "progress": 1.0, "kpi_id": kpi_id}

        if kpi.direction is KpiDirection.HIGHER_IS_BETTER:
            progress = min(kpi.current_value / kpi.target_value, 1.0)
            on_track = kpi.current_value >= kpi.target_value * kpi.met_threshold
        else:
            progress = min(kpi.target_value / max(kpi.current_value, 0.001), 1.0)
            on_track = kpi.current_value <= kpi.target_value * (2.0 - kpi.met_threshold)

        return {
            "on_track": on_track,
            "progress": round(progress, 4),
            "kpi_id": kpi_id,
            "current_value": kpi.current_value,
            "target_value": kpi.target_value,
        }


__all__ = ["GoalTracker"]
