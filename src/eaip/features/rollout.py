"""Rollout manager — gradual rollout, ramp-up, rollback, and scheduling."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from eaip.features.events import FlagRolloutChanged
from eaip.features.exceptions import FlagNotEnabledError, FlagNotFoundError, InvalidRolloutError
from eaip.features.manager import FeatureManager
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]

RolloutSchedule = dict[str, Any]


class RolloutManager:
    """Manages gradual rollouts, ramp-ups, rollbacks, and scheduled rollouts."""

    def __init__(
        self, manager: FeatureManager, event_callback: EventCallback | None = None
    ) -> None:
        self._manager = manager
        self._schedules: dict[str, RolloutSchedule] = {}
        self._rollout_status: dict[str, dict[str, Any]] = {}
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback
        self._manager.set_event_callback(callback)

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    async def gradual_rollout(self, flag_id: str, target_percentage: int) -> dict[str, Any]:
        """Gradually roll out a feature flag to a target percentage."""
        if not 0 <= target_percentage <= 100:
            raise InvalidRolloutError(
                "Target percentage must be between 0 and 100",
                context={"flag_id": flag_id, "target_percentage": target_percentage},
            )

        flag = await self._manager.get_flag(flag_id)
        if not flag.enabled:
            raise FlagNotEnabledError(
                f"Cannot roll out disabled flag: {flag_id}",
                context={"flag_id": flag_id},
            )

        previous = flag.rollout_percentage
        flag = await self._manager.update_flag(flag_id, rollout_percentage=target_percentage)
        self._emit(
            FlagRolloutChanged(
                flag_id=flag_id,
                key=flag.key,
                previous_percentage=previous,
                new_percentage=target_percentage,
            )
        )

        status = {
            "flag_id": flag_id,
            "previous_percentage": previous,
            "current_percentage": target_percentage,
            "target_percentage": target_percentage,
            "updated_at": utc_now(),
        }
        self._rollout_status[flag_id] = status
        return status

    async def ramp_up(self, flag_id: str, step_percentage: int) -> dict[str, Any]:
        """Increase rollout percentage by a step, capping at 100."""
        if not 0 <= step_percentage <= 100:
            raise InvalidRolloutError(
                "Step percentage must be between 0 and 100",
                context={"flag_id": flag_id, "step_percentage": step_percentage},
            )

        flag = await self._manager.get_flag(flag_id)
        if not flag.enabled:
            raise FlagNotEnabledError(
                f"Cannot ramp up disabled flag: {flag_id}",
                context={"flag_id": flag_id},
            )

        new_percentage = min(100, flag.rollout_percentage + step_percentage)
        previous = flag.rollout_percentage
        flag = await self._manager.update_flag(flag_id, rollout_percentage=new_percentage)
        self._emit(
            FlagRolloutChanged(
                flag_id=flag_id,
                key=flag.key,
                previous_percentage=previous,
                new_percentage=new_percentage,
            )
        )

        status = {
            "flag_id": flag_id,
            "previous_percentage": previous,
            "current_percentage": new_percentage,
            "target_percentage": 100,
            "updated_at": utc_now(),
        }
        self._rollout_status[flag_id] = status
        return status

    async def rollback(self, flag_id: str) -> dict[str, Any]:
        """Roll back a flag to 0% rollout and disable it."""
        flag = await self._manager.get_flag(flag_id)
        previous = flag.rollout_percentage
        flag = await self._manager.update_flag(flag_id, rollout_percentage=0, enabled=False)
        self._emit(
            FlagRolloutChanged(
                flag_id=flag_id,
                key=flag.key,
                previous_percentage=previous,
                new_percentage=0,
            )
        )

        status = {
            "flag_id": flag_id,
            "previous_percentage": previous,
            "current_percentage": 0,
            "target_percentage": 0,
            "rolled_back": True,
            "updated_at": utc_now(),
        }
        self._rollout_status[flag_id] = status
        return status

    async def get_rollout_status(self, flag_id: str) -> dict[str, Any] | None:
        """Return the current rollout status for a flag."""
        try:
            flag = await self._manager.get_flag(flag_id)
        except FlagNotFoundError:
            return None

        status = self._rollout_status.get(flag_id)
        if status is None:
            return {
                "flag_id": flag_id,
                "current_percentage": flag.rollout_percentage,
                "enabled": flag.enabled,
                "has_active_rollout": False,
            }
        return {**status, "has_active_rollout": True}

    async def schedule_rollout(self, flag_id: str, schedule: RolloutSchedule) -> dict[str, Any]:
        """Register a rollout schedule for eventual processing."""
        if "steps" not in schedule or not isinstance(schedule["steps"], list):
            raise InvalidRolloutError(
                "Schedule must contain a 'steps' list",
                context={"flag_id": flag_id},
            )
        for step in schedule["steps"]:
            if "percentage" not in step or "after_seconds" not in step:
                raise InvalidRolloutError(
                    "Each schedule step must have 'percentage' and 'after_seconds'",
                    context={"flag_id": flag_id},
                )

        self._schedules[flag_id] = {
            "flag_id": flag_id,
            "schedule": schedule,
            "registered_at": utc_now(),
        }
        return {
            "flag_id": flag_id,
            "scheduled": True,
            "steps": len(schedule["steps"]),
        }


__all__ = ["RolloutManager"]
