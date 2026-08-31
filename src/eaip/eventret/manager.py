"""EventRetentionManager — manage retention policies and jobs."""

from __future__ import annotations

from eaip.eventret.events import (
    PolicyApplied,
    PolicyCreated,
    RetentionJobCompleted,
    RetentionJobFailed,
)
from eaip.eventret.exceptions import PolicyNotFoundError
from eaip.eventret.models import (
    EventRetentionConfig,
    RetentionJob,
    RetentionJobStatus,
    RetentionPolicy,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class EventRetentionManager:
    """Central service for managing event retention policies and jobs."""

    def __init__(
        self, config: EventRetentionConfig | None = None, event_bus: EventBus | None = None
    ) -> None:
        self._config = config or EventRetentionConfig()
        self._policies: dict[str, RetentionPolicy] = {}
        self._jobs: dict[str, RetentionJob] = {}
        self._log = get_logger("eaip.eventret.service")
        self._event_bus = event_bus

    @property
    def config(self) -> EventRetentionConfig:
        return self._config

    async def create_policy(self, policy: RetentionPolicy) -> RetentionPolicy:
        """Create a new retention policy."""
        self._policies[policy.id] = policy
        if self._event_bus is not None:
            await self._event_bus.publish(
                PolicyCreated(
                    policy_id=policy.id,
                    name=policy.name,
                    action=policy.action,
                    enabled=policy.enabled,
                )
            )
        self._log.info(
            "eventret.policy.created",
            policy_id=policy.id,
            name=policy.name,
            action=policy.action.value,
        )
        return policy

    async def get_policy(self, policy_id: str) -> RetentionPolicy:
        """Get a retention policy by ID."""
        policy = self._policies.get(policy_id)
        if policy is None:
            raise PolicyNotFoundError(f"Retention policy not found: {policy_id}")
        return policy

    async def list_policies(self, enabled_only: bool = False) -> list[RetentionPolicy]:
        """List retention policies, optionally filtering to enabled only."""
        policies = list(self._policies.values())
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        return policies

    async def update_policy(self, policy_id: str, **updates: object) -> RetentionPolicy:
        """Update an existing retention policy."""
        policy = self._policies.get(policy_id)
        if policy is None:
            raise PolicyNotFoundError(f"Retention policy not found: {policy_id}")
        safe_keys = {
            "name",
            "event_type_pattern",
            "max_age_days",
            "max_count",
            "action",
            "enabled",
            "priority",
        }
        safe_updates = {k: v for k, v in updates.items() if k in safe_keys}
        updated = policy.model_copy(update=safe_updates)
        self._policies[policy_id] = updated
        self._log.info("eventret.policy.updated", policy_id=policy_id)
        return updated

    async def delete_policy(self, policy_id: str) -> None:
        """Delete a retention policy."""
        if policy_id not in self._policies:
            raise PolicyNotFoundError(f"Retention policy not found: {policy_id}")
        del self._policies[policy_id]
        self._log.info("eventret.policy.deleted", policy_id=policy_id)

    async def apply_policy(self, policy_id: str, job_id: str) -> RetentionJob:
        """Apply a retention policy, creating a retention job."""
        policy = self._policies.get(policy_id)
        if policy is None:
            raise PolicyNotFoundError(f"Retention policy not found: {policy_id}")
        if not policy.enabled:
            raise PolicyNotFoundError(f"Retention policy is disabled: {policy_id}")
        started = utc_now()
        job = RetentionJob(
            id=job_id,
            policy_id=policy_id,
            status=RetentionJobStatus.RUNNING,
            started_at=started,
        )
        self._jobs[job_id] = job
        affected = 0
        try:
            affected = await self._execute_policy(policy)
            completed = utc_now()
            delta = (completed - started).total_seconds()
            job = job.model_copy(
                update={
                    "affected_events": affected,
                    "status": RetentionJobStatus.COMPLETED,
                    "completed_at": completed,
                },
            )
            self._jobs[job_id] = job
            if self._event_bus is not None:
                await self._event_bus.publish(
                    PolicyApplied(
                        policy_id=policy_id,
                        name=policy.name,
                        affected_events=affected,
                        action=policy.action,
                    )
                )
                await self._event_bus.publish(
                    RetentionJobCompleted(
                        job_id=job_id,
                        policy_id=policy_id,
                        affected_events=affected,
                        duration_seconds=round(delta, 3),
                    )
                )
            self._log.info(
                "eventret.policy.applied",
                policy_id=policy_id,
                affected_events=affected,
            )
        except Exception as exc:
            completed = utc_now()
            error_msg = str(exc)
            job = job.model_copy(
                update={
                    "status": RetentionJobStatus.FAILED,
                    "completed_at": completed,
                    "error_message": error_msg,
                },
            )
            self._jobs[job_id] = job
            if self._event_bus is not None:
                await self._event_bus.publish(
                    RetentionJobFailed(job_id=job_id, policy_id=policy_id, error_message=error_msg)
                )
            self._log.error("eventret.policy.failed", policy_id=policy_id, error=error_msg)
        return job

    async def _execute_policy(self, policy: RetentionPolicy) -> int:
        """Execute a retention policy (stub — returns 0)."""
        return 0

    async def get_job(self, job_id: str) -> RetentionJob:
        """Get a retention job by ID."""
        job = self._jobs.get(job_id)
        if job is None:
            raise PolicyNotFoundError(f"Retention job not found: {job_id}")
        return job

    async def list_jobs(self, policy_id: str | None = None) -> list[RetentionJob]:
        """List retention jobs, optionally filtered by policy."""
        jobs = list(self._jobs.values())
        if policy_id is not None:
            jobs = [j for j in jobs if j.policy_id == policy_id]
        return jobs

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about policies and jobs."""
        total_policies = len(self._policies)
        enabled_policies = sum(1 for p in self._policies.values() if p.enabled)
        total_jobs = len(self._jobs)
        completed = sum(1 for j in self._jobs.values() if j.status == RetentionJobStatus.COMPLETED)
        failed = sum(1 for j in self._jobs.values() if j.status == RetentionJobStatus.FAILED)
        total_affected = sum(j.affected_events for j in self._jobs.values())
        return {
            "total_policies": total_policies,
            "enabled_policies": enabled_policies,
            "total_jobs": total_jobs,
            "completed": completed,
            "failed": failed,
            "total_affected_events": total_affected,
        }


__all__ = ["EventRetentionManager"]
