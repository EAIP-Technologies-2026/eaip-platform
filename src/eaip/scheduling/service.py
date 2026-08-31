from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from eaip.logging.context import get_logger
from eaip.scheduling.exceptions import (
    ScheduleNotFoundError,
    ScheduleValidationError,
)
from eaip.scheduling.models import (
    ScheduleDefinition,
    ScheduleExecution,
    ScheduleHealth,
    ScheduleKind,
    ScheduleStatus,
    ScheduleTargetType,
    ScheduleTrigger,
)
from eaip.scheduling.repository import ScheduleExecutionRepository, ScheduleRepository
from eaip.shared.time import utc_now

log = get_logger("eaip.scheduling.service")


def _resolve_tz(name: str) -> datetime.tzinfo:
    try:
        return ZoneInfo(name)
    except Exception:
        pass
    try:
        return ZoneInfo("UTC")
    except Exception:
        return UTC


class SchedulingService:
    def __init__(
        self,
        repo: ScheduleRepository | None = None,
        exec_repo: ScheduleExecutionRepository | None = None,
        event_bus: Any | None = None,
        workflow_engine: Any | None = None,
        mission_registry: Any | None = None,
        agent_runtime: Any | None = None,
    ) -> None:
        self._repo = repo or ScheduleRepository()
        self._exec_repo = exec_repo or ScheduleExecutionRepository()
        self._event_bus = event_bus
        self._workflow_engine = workflow_engine
        self._mission_registry = mission_registry
        self._agent_runtime = agent_runtime
        self._log = get_logger("eaip.scheduling.service")

    def _validate(self, definition: ScheduleDefinition) -> None:
        if not definition.id or not definition.id.strip():
            raise ScheduleValidationError("schedule id is required", field="id")
        if not definition.tenant_id or not definition.tenant_id.strip():
            raise ScheduleValidationError("tenant_id is required", field="tenant_id")
        if not definition.name or not definition.name.strip():
            raise ScheduleValidationError("schedule name is required", field="name")
        if not definition.target_id or not definition.target_id.strip():
            raise ScheduleValidationError("target_id is required", field="target_id")
        trigger = definition.trigger
        if trigger.kind == ScheduleKind.CRON and not trigger.cron_expr:
            raise ScheduleValidationError("cron_expr is required for cron schedules", field="cron_expr")
        if trigger.kind == ScheduleKind.INTERVAL and not trigger.interval_seconds:
            raise ScheduleValidationError(
                "interval_seconds is required for interval schedules", field="interval_seconds"
            )
        if trigger.kind in (ScheduleKind.ONE_TIME, ScheduleKind.DELAYED) and trigger.run_at is None:
            raise ScheduleValidationError(
                "run_at is required for one_time/delayed schedules", field="run_at"
            )
        if trigger.interval_seconds is not None and trigger.interval_seconds <= 0:
            raise ScheduleValidationError("interval_seconds must be positive", field="interval_seconds")

    def _calculate_next_run(
        self, trigger: ScheduleTrigger, now: datetime | None = None
    ) -> datetime | None:
        current = now or utc_now()
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)

        tz = _resolve_tz(trigger.timezone)
        local_now = current.astimezone(tz)

        if trigger.kind in (ScheduleKind.ONE_TIME, ScheduleKind.DELAYED):
            if trigger.run_at is None:
                return None
            run_at = trigger.run_at
            if run_at.tzinfo is None:
                run_at = run_at.replace(tzinfo=tz)
            run_at_utc = run_at.astimezone(UTC)
            if run_at_utc <= current:
                return None
            return run_at_utc

        if trigger.kind == ScheduleKind.INTERVAL:
            interval = trigger.interval_seconds or 0
            if interval <= 0:
                return None
            if trigger.run_at is not None:
                base = trigger.run_at
                if base.tzinfo is None:
                    base = base.replace(tzinfo=UTC)
                if base > current:
                    return base.astimezone(UTC)
            return current + timedelta(seconds=interval)

        if trigger.kind in (ScheduleKind.CRON, ScheduleKind.RECURRING):
            if trigger.cron_expr:
                try:
                    from croniter import croniter  # type: ignore[import-untyped]

                    base = local_now
                    itr = croniter(trigger.cron_expr, base)
                    nxt = itr.get_next(datetime)
                    if nxt.tzinfo is None:
                        nxt = nxt.replace(tzinfo=tz)
                    return nxt.astimezone(UTC)
                except ImportError:
                    pass
                except Exception as exc:
                    self._log.warning("cron.parse_failed", expr=trigger.cron_expr, error=str(exc))
                    return current + timedelta(hours=1)
                return current + timedelta(hours=1)
            if trigger.interval_seconds:
                return current + timedelta(seconds=trigger.interval_seconds)
            return current + timedelta(hours=1)

        return None

    async def create_schedule(self, definition: ScheduleDefinition) -> ScheduleDefinition:
        self._validate(definition)
        next_run = self._calculate_next_run(definition.trigger)
        to_create = definition.model_copy(update={"next_run_at": next_run, "updated_at": utc_now()})
        result = await self._repo.create(to_create)
        self._publish("eaip.scheduling.created", {"schedule_id": result.id, "tenant_id": result.tenant_id})
        self._log.info("schedule.created", schedule_id=result.id, tenant_id=result.tenant_id)
        return result

    async def get_schedule(self, schedule_id: str, tenant_id: str) -> ScheduleDefinition:
        found = await self._repo.get(schedule_id, tenant_id)
        if found is None:
            raise ScheduleNotFoundError(schedule_id, tenant_id)
        return found

    async def list_schedules(
        self,
        tenant_id: str,
        status: ScheduleStatus | str | None = None,
        kind: ScheduleKind | str | None = None,
        limit: int = 100,
        priority: int | None = None,
    ) -> list[ScheduleDefinition]:
        return await self._repo.list_by_tenant(tenant_id, status=status, kind=kind, priority=priority, limit=limit)

    async def update_schedule(
        self, schedule_id: str, tenant_id: str, updates: dict[str, Any]
    ) -> ScheduleDefinition:
        existing = await self._repo.get(schedule_id, tenant_id)
        if existing is None:
            raise ScheduleNotFoundError(schedule_id, tenant_id)
        if "trigger" in updates and isinstance(updates["trigger"], dict):
            trigger = ScheduleTrigger.model_validate(updates["trigger"])
            updates["trigger"] = trigger
            updates["next_run_at"] = self._calculate_next_run(trigger)
        updates["updated_at"] = utc_now()
        updated = await self._repo.update(schedule_id, tenant_id, updates)
        if updated is None:
            raise ScheduleNotFoundError(schedule_id, tenant_id)
        self._publish("eaip.scheduling.updated", {"schedule_id": schedule_id, "tenant_id": tenant_id})
        return updated

    async def pause(self, schedule_id: str, tenant_id: str) -> ScheduleDefinition:
        return await self.update_schedule(schedule_id, tenant_id, {"status": ScheduleStatus.PAUSED})

    async def resume(self, schedule_id: str, tenant_id: str) -> ScheduleDefinition:
        existing = await self.get_schedule(schedule_id, tenant_id)
        updates: dict[str, Any] = {"status": ScheduleStatus.ACTIVE, "updated_at": utc_now()}
        if existing.next_run_at is None or existing.next_run_at <= utc_now():
            nxt = self._calculate_next_run(existing.trigger)
            if nxt is not None:
                updates["next_run_at"] = nxt
        updated = await self._repo.update(schedule_id, tenant_id, updates)
        if updated is None:
            raise ScheduleNotFoundError(schedule_id, tenant_id)
        self._publish("eaip.scheduling.resumed", {"schedule_id": schedule_id, "tenant_id": tenant_id})
        return updated

    async def cancel(self, schedule_id: str, tenant_id: str) -> ScheduleDefinition:
        return await self.update_schedule(schedule_id, tenant_id, {"status": ScheduleStatus.CANCELLED})

    async def reschedule(
        self, schedule_id: str, tenant_id: str, new_trigger: ScheduleTrigger | dict[str, Any]
    ) -> ScheduleDefinition:
        if isinstance(new_trigger, dict):
            new_trigger = ScheduleTrigger.model_validate(new_trigger)
        nxt = self._calculate_next_run(new_trigger)
        return await self.update_schedule(
            schedule_id, tenant_id, {"trigger": new_trigger, "next_run_at": nxt}
        )

    async def _check_dependencies(self, definition: ScheduleDefinition) -> bool:
        if not definition.dependencies:
            return True
        for dep_id in definition.dependencies:
            execs = await self._exec_repo.list_by_schedule(dep_id, definition.tenant_id, limit=5)
            if not execs:
                dep_def = await self._repo.get(dep_id, definition.tenant_id)
                if dep_def is None:
                    return False
                dep_execs = await self._exec_repo.list_by_schedule(dep_id, definition.tenant_id, limit=1)
                if not dep_execs:
                    return False
                continue
            has_success = any(e.status in ("completed", "success", "succeeded") for e in execs)
            if not has_success:
                return False
        return True

    async def _dispatch(self, definition: ScheduleDefinition) -> str:
        target_type = definition.target_type
        target_id = definition.target_id

        if target_type == ScheduleTargetType.WORKFLOW:
            if self._workflow_engine is not None:
                try:
                    if hasattr(self._workflow_engine, "execute"):
                        result = await self._workflow_engine.execute(target_id, {})
                        if isinstance(result, dict):
                            return str(result.get("result") or result.get("output") or result)
                        return str(result) if result is not None else "workflow executed"
                    if hasattr(self._workflow_engine, "run"):
                        result = await self._workflow_engine.run(target_id)
                        return str(result) if result is not None else "workflow executed"
                except Exception as exc:
                    raise RuntimeError(f"workflow dispatch failed: {exc}") from exc
            return f"workflow:{target_id} dispatched (no engine)"

        if target_type == ScheduleTargetType.MISSION:
            if self._mission_registry is not None:
                try:
                    if hasattr(self._mission_registry, "execute"):
                        result = await self._mission_registry.execute(target_id)
                        return str(result) if result is not None else "mission executed"
                    if hasattr(self._mission_registry, "run"):
                        result = await self._mission_registry.run(target_id)
                        return str(result) if result is not None else "mission executed"
                    if hasattr(self._mission_registry, "get"):
                        mission = await self._mission_registry.get(target_id)  # type: ignore[attr-defined]
                        return f"mission:{target_id} resolved: {mission}"
                except Exception as exc:
                    raise RuntimeError(f"mission dispatch failed: {exc}") from exc
            return f"mission:{target_id} dispatched (no registry)"

        if target_type == ScheduleTargetType.AGENT_ACTION:
            if self._agent_runtime is not None:
                try:
                    if hasattr(self._agent_runtime, "execute"):
                        result = await self._agent_runtime.execute(target_id, {})  # type: ignore[attr-defined]
                        return str(result) if result is not None else "agent action executed"
                    if hasattr(self._agent_runtime, "run"):
                        result = await self._agent_runtime.run(target_id)  # type: ignore[attr-defined]
                        return str(result) if result is not None else "agent action executed"
                    if hasattr(self._agent_runtime, "create_run"):
                        result = await self._agent_runtime.create_run(target_id, {})  # type: ignore[attr-defined]
                        return str(result) if result is not None else "agent action executed"
                except Exception as exc:
                    raise RuntimeError(f"agent dispatch failed: {exc}") from exc
            return f"agent_action:{target_id} dispatched (no runtime)"

        return f"target:{target_id} dispatched"

    async def execute(self, schedule_id: str, tenant_id: str) -> ScheduleExecution:
        definition = await self.get_schedule(schedule_id, tenant_id)

        if definition.status != ScheduleStatus.ACTIVE:
            raise ScheduleValidationError(
                f"schedule {schedule_id!r} is not active (status={definition.status.value})"
            )

        if not await self._check_dependencies(definition):
            raise ScheduleValidationError(
                f"schedule {schedule_id!r} dependencies not satisfied",
                field="dependencies",
            )

        execution = ScheduleExecution(
            id=uuid.uuid4().hex,
            schedule_id=schedule_id,
            tenant_id=tenant_id,
            status="running",
            attempt=1,
            scheduled_at=definition.next_run_at or utc_now(),
            started_at=utc_now(),
        )
        await self._exec_repo.create(execution)

        last_error: str | None = None
        result_text = ""
        max_retries = definition.retry_policy.max_retries
        delay = definition.retry_policy.delay_seconds
        multiplier = definition.retry_policy.backoff_multiplier

        for attempt in range(1, max_retries + 2):
            try:
                result_text = await self._dispatch(definition)
                execution = execution.model_copy(
                    update={
                        "status": "completed",
                        "attempt": attempt,
                        "completed_at": utc_now(),
                        "result": result_text,
                        "error": None,
                    }
                )
                await self._exec_repo.create(execution)
                break
            except Exception as exc:
                last_error = str(exc)
                if attempt > max_retries:
                    execution = execution.model_copy(
                        update={
                            "status": "failed",
                            "attempt": attempt,
                            "completed_at": utc_now(),
                            "result": "",
                            "error": last_error,
                        }
                    )
                    await self._exec_repo.create(execution)
                    self._log.error(
                        "schedule.execute.failed",
                        schedule_id=schedule_id,
                        tenant_id=tenant_id,
                        error=last_error,
                        attempt=attempt,
                    )
                    break
                backoff = delay * (multiplier ** (attempt - 1))
                self._log.warning(
                    "schedule.execute.retry",
                    schedule_id=schedule_id,
                    attempt=attempt,
                    backoff_s=backoff,
                    error=last_error,
                )
                await asyncio.sleep(backoff)
                execution = execution.model_copy(update={"attempt": attempt + 1})

        now = utc_now()
        if definition.trigger.kind in (ScheduleKind.ONE_TIME, ScheduleKind.DELAYED):
            await self._repo.update(
                schedule_id,
                tenant_id,
                {
                    "status": ScheduleStatus.COMPLETED if execution.status == "completed" else ScheduleStatus.FAILED,
                    "last_run_at": now,
                    "next_run_at": None,
                    "updated_at": now,
                },
            )
        else:
            nxt = self._calculate_next_run(definition.trigger, now=now)
            patch: dict[str, Any] = {"last_run_at": now, "updated_at": now}
            if nxt is not None:
                patch["next_run_at"] = nxt
            if execution.status == "failed":
                patch["status"] = ScheduleStatus.FAILED
            await self._repo.update(schedule_id, tenant_id, patch)

        event_type = "eaip.scheduling.executed" if execution.status == "completed" else "eaip.scheduling.failed"
        self._publish(event_type, {"schedule_id": schedule_id, "tenant_id": tenant_id, "status": execution.status})

        return execution

    async def get_due(self, tenant_id: str, now: datetime | None = None) -> list[ScheduleDefinition]:
        ts = now or utc_now()
        return await self._repo.get_due(tenant_id, ts)

    async def get_all_due(self, now: datetime | None = None) -> list[ScheduleDefinition]:
        ts = now or utc_now()
        return await self._repo.get_all_due(ts)

    async def get_upcoming(self, tenant_id: str, horizon_hours: int = 24) -> list[ScheduleDefinition]:
        now = utc_now()
        horizon = now + timedelta(hours=horizon_hours)
        all_schedules = await self._repo.list_by_tenant(tenant_id, status=ScheduleStatus.ACTIVE, limit=1000)
        return [s for s in all_schedules if s.next_run_at is not None and s.next_run_at <= horizon and s.next_run_at >= now]

    async def get_health(self, schedule_id: str, tenant_id: str) -> ScheduleHealth:
        definition = await self.get_schedule(schedule_id, tenant_id)
        execs = await self._exec_repo.list_by_schedule(schedule_id, tenant_id, limit=1000)
        total = len(execs)
        failed = sum(1 for e in execs if e.status in ("failed", "error"))
        failure_rate = (failed / total) if total > 0 else 0.0
        health_score = max(0.0, 1.0 - failure_rate)
        overdue = 0
        if definition.status == ScheduleStatus.ACTIVE and definition.next_run_at is not None:
            if definition.next_run_at < utc_now():
                overdue = 1
        if definition.status == ScheduleStatus.OVERDUE:
            overdue = 1
        return ScheduleHealth(
            schedule_id=schedule_id,
            health_score=round(health_score, 4),
            failure_rate=round(failure_rate, 4),
            overdue_count=overdue,
            total_executions=total,
            failed_executions=failed,
        )

    async def get_stats(self, tenant_id: str) -> dict[str, Any]:
        all_schedules = await self._repo.list_by_tenant(tenant_id, limit=10000)
        by_status: dict[str, int] = {}
        for s in all_schedules:
            by_status[s.status.value] = by_status.get(s.status.value, 0) + 1
        by_kind: dict[str, int] = {}
        for s in all_schedules:
            by_kind[s.trigger.kind.value] = by_kind.get(s.trigger.kind.value, 0) + 1
        execs = await self._exec_repo.list_by_tenant(tenant_id, limit=10000)
        return {
            "total": len(all_schedules),
            "by_status": by_status,
            "by_kind": by_kind,
            "total_executions": len(execs),
            "tenant_id": tenant_id,
        }

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if self._event_bus is None:
            return
        try:
            event: Any = {"type": event_type, **payload}
            if hasattr(self._event_bus, "publish"):
                result = self._event_bus.publish(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
        except Exception:
            self._log.warning("event.publish.failed", event_type=event_type)


__all__ = ["SchedulingService"]
