"""Decision Intelligence persistence repository."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.persistence import _TenantRepository
from eaip.decisions.models import DecisionLog
from eaip.shared.time import utc_now


class DecisionRepository(_TenantRepository):
    """Repository for managing decision logs."""

    def __init__(self, db: Any) -> None:
        super().__init__(db, table_name="decision_logs")

    async def get_by_id(self, id: str, tenant_id: str) -> DecisionLog | None:
        row = await self._db.fetch_row(
            f"SELECT * FROM {self._table_name} WHERE id = $1 AND tenant_id = $2",
            id,
            tenant_id,
        )
        if not row:
            return None
        return DecisionLog(
            id=row["id"],
            tenant_id=row["tenant_id"],
            decision_type=row["decision_type"],
            context=json.loads(row["context"]),
            outcome=json.loads(row["outcome"]),
            timestamp=row["timestamp"],
        )

    async def save(self, log: DecisionLog) -> None:
        await self._db.execute(
            f"""
            INSERT INTO {self._table_name} 
            (id, tenant_id, decision_type, context, outcome, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE SET
                decision_type = EXCLUDED.decision_type,
                context = EXCLUDED.context,
                outcome = EXCLUDED.outcome,
                timestamp = EXCLUDED.timestamp
            """,
            log.id,
            log.tenant_id,
            log.decision_type,
            json.dumps(log.context),
            json.dumps(log.outcome),
            log.timestamp,
        )

    async def list_by_type(self, decision_type: str, tenant_id: str, limit: int = 100) -> list[DecisionLog]:
        rows = await self._db.fetch_rows(
            f"""
            SELECT * FROM {self._table_name}
            WHERE tenant_id = $1 AND decision_type = $2
            ORDER BY timestamp DESC
            LIMIT $3
            """,
            tenant_id,
            decision_type,
            limit,
        )
        return [
            DecisionLog(
                id=row["id"],
                tenant_id=row["tenant_id"],
                decision_type=row["decision_type"],
                context=json.loads(row["context"]),
                outcome=json.loads(row["outcome"]),
                timestamp=row["timestamp"],
            )
            for row in rows
        ]
