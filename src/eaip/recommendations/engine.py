"""Recommendations Engine."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.infrastructure.persistence import RecommendationRepository
from eaip.logging.context import get_logger
from eaip.recommendations.models import Recommendation, RecommendationStatus
from eaip.shared.time import utc_now


class RecommendationEngine:
    """Core logic for Recommendations Service."""

    def __init__(self, repository: RecommendationRepository) -> None:
        self._repository = repository
        self._log = get_logger("eaip.recommendations.engine")

    async def create_recommendation(
        self, title: str, description: str, score: float, metadata: dict[str, Any], tenant_id: str
    ) -> Recommendation:
        """Create a new recommendation."""
        rec = Recommendation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            description=description,
            score=score,
            metadata=metadata,
        )
        await self._repository.save(rec)
        self._log.info("recommendation.created", rec_id=rec.id, title=title)
        return rec

    async def list_pending(self, tenant_id: str, limit: int = 100) -> list[Recommendation]:
        """List pending recommendations."""
        return await self._repository.list_pending(tenant_id=tenant_id, limit=limit)

    async def update_status(self, rec_id: str, tenant_id: str, status: RecommendationStatus) -> Recommendation:
        """Update status of a recommendation."""
        rec = await self._repository.get_by_id(rec_id, tenant_id)
        if not rec:
            raise ValueError(f"Recommendation {rec_id} not found")

        updated = rec.model_copy(update={"status": status, "updated_at": utc_now()})
        await self._repository.save(updated)
        self._log.info("recommendation.updated", rec_id=rec_id, status=status.value)
        return updated
