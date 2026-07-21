"""Failover automation — initiate, complete, rollback, and monitor failover events."""

from __future__ import annotations

import time
import uuid
from typing import Any

from eaip.dr.events import (
    FailoverCompleted,
    FailoverRolledBack,
    FailoverStarted,
)
from eaip.dr.exceptions import FailoverError, PlanNotFoundError
from eaip.dr.models import (
    DrPlan,
    FailoverEvent,
    FailoverEventStatus,
    PlanStatus,
)
from eaip.logging.context import get_logger


class FailoverManager:
    """Manages failover events for disaster recovery plans."""

    def __init__(self, event_bus: Any = None) -> None:
        self._events: dict[str, FailoverEvent] = {}
        self._plans: dict[str, DrPlan] = {}
        self._config: dict[str, Any] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.dr.failover")

    def register_plan(self, plan: DrPlan) -> None:
        self._plans[plan.id] = plan

    def register_config(self, plan_id: str, auto_failover: bool = False) -> None:
        self._config[plan_id] = {"auto_failover_enabled": auto_failover}

    async def initiate_failover(self, plan_id: str, reason: str = "") -> FailoverEvent:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise PlanNotFoundError(
                f"DR plan {plan_id!r} not found",
                context={"plan_id": plan_id},
            )

        if plan.status not in (PlanStatus.ACTIVE, PlanStatus.TESTED):
            raise FailoverError(
                f"Plan {plan_id} is not active for failover (status: {plan.status})",
                context={"plan_id": plan_id, "status": str(plan.status)},
            )

        event = FailoverEvent(
            id=str(uuid.uuid4()),
            plan_id=plan_id,
            reason=reason,
            status=FailoverEventStatus.IN_PROGRESS,
        )
        self._events[event.id] = event

        if self._event_bus is not None:
            self._event_bus.publish(FailoverStarted(event=event))

        self._log.info("dr.failover.initiated", plan_id=plan_id, event_id=event.id, reason=reason)
        return event

    async def complete_failover(
        self, event_id: str, duration_ms: float | None = None
    ) -> FailoverEvent:
        event = self._events.get(event_id)
        if event is None:
            raise FailoverError(
                f"Failover event {event_id!r} not found",
                context={"event_id": event_id},
            )

        if event.status != FailoverEventStatus.IN_PROGRESS:
            raise FailoverError(
                f"Cannot complete event {event_id} in status {event.status}",
                context={"event_id": event_id, "status": str(event.status)},
            )

        completed = event.model_copy(
            update={
                "status": FailoverEventStatus.COMPLETED,
                "completed_at": None,
                "duration_ms": duration_ms or 0.0,
            },
        )
        self._events[event_id] = completed

        if self._event_bus is not None:
            self._event_bus.publish(FailoverCompleted(event=completed))

        self._log.info("dr.failover.completed", event_id=event_id)
        return completed

    async def rollback_failover(self, event_id: str) -> FailoverEvent:
        event = self._events.get(event_id)
        if event is None:
            raise FailoverError(
                f"Failover event {event_id!r} not found",
                context={"event_id": event_id},
            )

        if event.status not in (FailoverEventStatus.IN_PROGRESS, FailoverEventStatus.COMPLETED):
            raise FailoverError(
                f"Cannot rollback event {event_id} in status {event.status}",
                context={"event_id": event_id, "status": str(event.status)},
            )

        rolled_back = event.model_copy(
            update={
                "status": FailoverEventStatus.ROLLED_BACK,
                "completed_at": None,
                "duration_ms": (time.monotonic() * 1000),
            },
        )
        self._events[event_id] = rolled_back

        if self._event_bus is not None:
            self._event_bus.publish(FailoverRolledBack(event=rolled_back))

        self._log.info("dr.failover.rolled_back", event_id=event_id)
        return rolled_back

    async def get_failover_status(self, event_id: str) -> FailoverEvent:
        event = self._events.get(event_id)
        if event is None:
            raise FailoverError(
                f"Failover event {event_id!r} not found",
                context={"event_id": event_id},
            )
        return event

    async def list_failover_history(self, plan_id: str, limit: int = 10) -> list[FailoverEvent]:
        events = [e for e in self._events.values() if e.plan_id == plan_id]
        events.sort(key=lambda e: e.started_at, reverse=True)
        return events[:limit]

    async def is_autofailover_enabled(self, plan_id: str) -> bool:
        cfg = self._config.get(plan_id, {})
        return bool(cfg.get("auto_failover_enabled", False))

    async def check_health(self, plan_id: str) -> bool:
        plan = self._plans.get(plan_id)
        if plan is None:
            return False
        recent_events = await self.list_failover_history(plan_id, limit=1)
        if not recent_events:
            return True
        return recent_events[0].status != FailoverEventStatus.FAILED


__all__ = ["FailoverManager"]
