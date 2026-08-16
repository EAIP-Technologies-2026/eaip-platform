"""Recommendations persistence repository."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from eaip.infrastructure.persistence import _TenantRepository
from eaip.recommendations.models import Recommendation, RecommendationStatus
from eaip.shared.time import utc_now


class RecommendationRepository(_TenantRepository):
    """Repository for managing recommendations."""

    def __init__(self, db: Any) -> None:
        super().__init__(db, table_name="recommendations")

    async def get_by_id(self, id: str, tenant_id: str) -> Recommendation | None:
        row = await self._db.fetch_row(
            f"SELECT * FROM {self._table_name} WHERE id = $1 AND tenant_id = $2",
            id,
            tenant_id,
        )
        if not row:
            return None
        return Recommendation(
            id=row["id"],
            tenant_id=row["tenant_id"],
            title=row["title"],
            description=row["description"],
            score=row["score"],
            metadata=json.loads(row["metadata"]),
            status=RecommendationStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def save(self, rec: Recommendation) -> None:
        await self._db.execute(
            f"""
            INSERT INTO {self._table_name} 
            (id, tenant_id, title, description, score, metadata, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                score = EXCLUDED.score,
                metadata = EXCLUDED.metadata,
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at
            """,
            rec.id,
            rec.tenant_id,
            rec.title,
            rec.description,
            rec.score,
            json.dumps(rec.metadata),
            rec.status.value,
            rec.created_at,
            rec.updated_at,
        )

    async def list_pending(self, tenant_id: str, limit: int = 100) -> list[Recommendation]:
        rows = await self._db.fetch_rows(
            f"""
            SELECT * FROM {self._table_name}
            WHERE tenant_id = $1 AND status = 'pending'
            ORDER BY score DESC, created_at DESC
            LIMIT $2
            """,
            tenant_id,
            limit,
        )
        return [
            Recommendation(
                id=row["id"],
                tenant_id=row["tenant_id"],
                title=row["title"],
                description=row["description"],
                score=row["score"],
                metadata=json.loads(row["metadata"]),
                status=RecommendationStatus(row["status"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]
