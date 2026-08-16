"""Intelligence Pulse Engine."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.infrastructure.persistence import PulseRepository
from eaip.logging.context import get_logger
from eaip.pulse.models import PulseMetric
from eaip.shared.time import utc_now


class PulseEngine:
    """Core logic for Intelligence Pulse."""

    def __init__(self, repository: PulseRepository) -> None:
        self._repository = repository
        self._log = get_logger("eaip.pulse.engine")

    async def record_metric(
        self, name: str, value: float, dimensions: dict[str, Any], tenant_id: str
    ) -> PulseMetric:
        """Record a new pulse metric."""
        metric = PulseMetric(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            value=value,
            dimensions=dimensions,
            timestamp=utc_now(),
        )
        await self._repository.save(metric)
        self._log.info("pulse.metric.recorded", metric_id=metric.id, name=metric.name)
        return metric

    async def list_metrics(self, name: str, tenant_id: str, limit: int = 100) -> list[PulseMetric]:
        """List metrics by name."""
        return await self._repository.list_by_name(name=name, tenant_id=tenant_id, limit=limit)
