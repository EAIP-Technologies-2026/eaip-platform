"""Decision Intelligence Engine."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.decisions.models import DecisionLog
from eaip.infrastructure.persistence import DecisionRepository
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class DecisionEngine:
    """Core logic for Decision Intelligence."""

    def __init__(self, repository: DecisionRepository) -> None:
        self._repository = repository
        self._log = get_logger("eaip.decisions.engine")

    async def log_decision(
        self, decision_type: str, context: dict[str, Any], outcome: dict[str, Any], tenant_id: str
    ) -> DecisionLog:
        """Log a decision."""
        log = DecisionLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            decision_type=decision_type,
            context=context,
            outcome=outcome,
            timestamp=utc_now(),
        )
        await self._repository.save(log)
        self._log.info("decision.logged", decision_id=log.id, type=decision_type)
        return log

    async def list_decisions(self, decision_type: str, tenant_id: str, limit: int = 100) -> list[DecisionLog]:
        """List decisions by type."""
        return await self._repository.list_by_type(decision_type=decision_type, tenant_id=tenant_id, limit=limit)
