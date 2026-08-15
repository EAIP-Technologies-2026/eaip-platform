from __future__ import annotations

import asyncio
from typing import Any

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.observability.events import SloCreated, SloStatusChanged, SloViolated
from eaip.observability.exceptions import SloNotFoundError
from eaip.observability.models import ObservabilityConfig, ServiceLevelObjective, SloStatus


class SliService:
    name: str = "observability.slo"

    def __init__(
        self,
        config: ObservabilityConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config = config or ObservabilityConfig()
        self._slos: dict[str, ServiceLevelObjective] = {}
        self._log = get_logger("eaip.observability.slo")
        self._event_bus = event_bus

    def create_slo(self, slo: ServiceLevelObjective) -> ServiceLevelObjective:
        self._slos[slo.id] = slo
        self._log.info("slo.created", id=slo.id, name=slo.name)
        if self._event_bus is not None:
            asyncio.ensure_future(
                self._event_bus.publish(
                    SloCreated(slo_id=slo.id, slo_name=slo.name, target_percent=slo.target_percent)
                )
            )
        return slo

    def get_slo(self, slo_id: str) -> ServiceLevelObjective:
        slo = self._slos.get(slo_id)
        if slo is None:
            raise SloNotFoundError(f"SLO {slo_id!r} not found")
        return slo

    def update_slo(self, slo_id: str, **updates: Any) -> ServiceLevelObjective:
        slo = self.get_slo(slo_id)
        updated = slo.model_copy(update=updates)
        self._slos[slo_id] = updated
        self._log.info("slo.updated", id=slo_id)
        return updated

    def delete_slo(self, slo_id: str) -> None:
        self.get_slo(slo_id)
        del self._slos[slo_id]
        self._log.info("slo.deleted", id=slo_id)

    def list_slos(
        self,
        status_filter: SloStatus | None = None,
    ) -> list[ServiceLevelObjective]:
        result = list(self._slos.values())
        if status_filter is not None:
            result = [s for s in result if s.status == status_filter]
        return result

    async def evaluate_slo(self, slo_id: str) -> ServiceLevelObjective:
        slo = self.get_slo(slo_id)
        if slo.status == "paused":
            return slo

        previous_status = slo.status
        current_value = await self._compute_sli_value(slo)
        burn_rate = await self.calculate_burn_rate(slo, slo.window_seconds)

        status: SloStatus = "active"
        if current_value < slo.target_value * (slo.target_percent / 100.0):
            status = "violated"
        elif burn_rate > slo.burn_rate_threshold:
            status = "at_risk"
        else:
            status = "active"

        updated = slo.model_copy(
            update={
                "current_value": current_value,
                "current_burn_rate": burn_rate,
                "status": status,
            },
        )
        self._slos[slo_id] = updated

        if status != previous_status:
            if self._event_bus is not None:
                await self._event_bus.publish(
                    SloStatusChanged(
                        slo_id=slo_id,
                        slo_name=slo.name,
                        previous_status=previous_status,
                        new_status=status,
                        current_value=current_value,
                    )
                )

        if status == "violated":
            if self._event_bus is not None:
                await self._event_bus.publish(
                    SloViolated(
                        slo_id=slo_id,
                        slo_name=slo.name,
                        target_value=slo.target_value,
                        current_value=current_value,
                        burn_rate=burn_rate,
                    )
                )

        self._log.info("slo.evaluated", id=slo_id, status=status, value=current_value)
        return updated

    async def evaluate_all_slos(self) -> list[ServiceLevelObjective]:
        results: list[ServiceLevelObjective] = []
        for slo_id in list(self._slos.keys()):
            updated = await self.evaluate_slo(slo_id)
            results.append(updated)
        self._log.info("slo.all_evaluated", count=len(results))
        return results

    async def get_slo_status(self, slo_id: str) -> dict[str, Any]:
        slo = self.get_slo(slo_id)
        return {
            "id": slo.id,
            "name": slo.name,
            "status": slo.status,
            "current_value": slo.current_value,
            "current_burn_rate": slo.current_burn_rate,
            "target_percent": slo.target_percent,
            "window_seconds": slo.window_seconds,
            "burn_rate_threshold": slo.burn_rate_threshold,
        }

    async def calculate_burn_rate(
        self,
        slo: ServiceLevelObjective,
        window: int,
    ) -> float:
        error_rate = 1.0 - (slo.current_value / 100.0)
        allowed_error_rate = 1.0 - (slo.target_percent / 100.0)
        if allowed_error_rate <= 0:
            return 0.0
        return error_rate / allowed_error_rate

    async def check_burn_rate_alert(self, slo: ServiceLevelObjective) -> bool:
        if not slo.alert_on_burn_rate:
            return False
        burn_rate = await self.calculate_burn_rate(slo, slo.window_seconds)
        return burn_rate > slo.burn_rate_threshold

    async def _compute_sli_value(self, slo: ServiceLevelObjective) -> float:
        return slo.current_value

    @property
    def config(self) -> ObservabilityConfig:
        return self._config

    @config.setter
    def config(self, value: ObservabilityConfig) -> None:
        self._config = value


__all__ = ["SliService"]
