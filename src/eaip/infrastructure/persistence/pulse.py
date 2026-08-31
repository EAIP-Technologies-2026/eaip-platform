"""Pulse Metrics persistence repository."""

from __future__ import annotations

import json
from typing import Any

from eaip.infrastructure.persistence import _TenantRepository
from eaip.pulse.models import PulseMetric


class PulseRepository(_TenantRepository):
    """Repository for managing intelligence pulse metrics."""

    def __init__(self, db: Any) -> None:
        self._db = db
        self._table_name = "pulse_metrics"

    async def get_by_id(self, id: str, tenant_id: str) -> PulseMetric | None:
        row = await self._db.fetch_row(
            f"SELECT * FROM {self._table_name} WHERE id = $1 AND tenant_id = $2",
            id,
            tenant_id,
        )
        if not row:
            return None
        return PulseMetric(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            value=row["value"],
            dimensions=json.loads(row["dimensions"]),
            timestamp=row["timestamp"],
        )

    async def save(self, metric: PulseMetric) -> None:
        await self._db.execute(
            f"""
            INSERT INTO {self._table_name} 
            (id, tenant_id, name, value, dimensions, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                value = EXCLUDED.value,
                dimensions = EXCLUDED.dimensions,
                timestamp = EXCLUDED.timestamp
            """,
            metric.id,
            metric.tenant_id,
            metric.name,
            metric.value,
            json.dumps(metric.dimensions),
            metric.timestamp,
        )

    async def list_by_name(self, name: str, tenant_id: str, limit: int = 100) -> list[PulseMetric]:
        rows = await self._db.fetch_rows(
            f"""
            SELECT * FROM {self._table_name}
            WHERE tenant_id = $1 AND name = $2
            ORDER BY timestamp DESC
            LIMIT $3
            """,
            tenant_id,
            name,
            limit,
        )
        return [
            PulseMetric(
                id=row["id"],
                tenant_id=row["tenant_id"],
                name=row["name"],
                value=row["value"],
                dimensions=json.loads(row["dimensions"]),
                timestamp=row["timestamp"],
            )
            for row in rows
        ]
