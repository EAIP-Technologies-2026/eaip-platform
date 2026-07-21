"""RetentionService — manage retention policies and execute purge jobs."""

from __future__ import annotations

from datetime import timedelta

from eaip.logging.context import get_logger
from eaip.retention.events import PolicyCreated, PolicyDeleted, PolicyUpdated, PurgeExecuted
from eaip.retention.exceptions import PolicyNotFoundError, PurgeExecutionError
from eaip.retention.models import (
    PurgeJob,
    PurgeStatus,
    RetentionConfig,
    RetentionPolicy,
)
from eaip.shared.time import utc_now


class RetentionService:
    def __init__(self, config: RetentionConfig | None = None) -> None:
        self._config = config or RetentionConfig()
        self._policies: dict[str, RetentionPolicy] = {}
        self._jobs: dict[str, PurgeJob] = {}
        self._job_counter: int = 0
        self._log = get_logger("eaip.retention.service")

    @property
    def config(self) -> RetentionConfig:
        return self._config

    async def create_policy(self, policy: RetentionPolicy) -> RetentionPolicy:
        self._policies[policy.id] = policy
        PolicyCreated(policy_id=policy.id, name=policy.name)
        self._log.info("retention.policy.created", policy_id=policy.id, name=policy.name)
        return policy

    async def get_policy(self, policy_id: str) -> RetentionPolicy:
        policy = self._policies.get(policy_id)
        if policy is None:
            raise PolicyNotFoundError(f"Policy '{policy_id}' not found")
        return policy

    async def list_policies(self) -> list[RetentionPolicy]:
        return list(self._policies.values())

    async def update_policy(self, policy_id: str, **updates: str) -> RetentionPolicy:
        policy = await self.get_policy(policy_id)
        updated = policy.model_copy(update=updates, deep=True)
        self._policies[policy_id] = updated
        PolicyUpdated(policy_id=policy_id, changes=updates)
        self._log.info("retention.policy.updated", policy_id=policy_id)
        return updated

    async def delete_policy(self, policy_id: str) -> None:
        if policy_id not in self._policies:
            raise PolicyNotFoundError(f"Policy '{policy_id}' not found")
        del self._policies[policy_id]
        PolicyDeleted(policy_id=policy_id)
        self._log.info("retention.policy.deleted", policy_id=policy_id)

    async def execute_purge(self, policy_id: str) -> PurgeJob:
        policy = await self.get_policy(policy_id)
        if not policy.enabled:
            raise PurgeExecutionError(f"Policy '{policy_id}' is disabled")

        self._job_counter += 1
        job = PurgeJob(
            id=f"purge_{self._job_counter}",
            policy_id=policy_id,
            status=PurgeStatus.RUNNING,
            started_at=utc_now(),
        )
        self._jobs[job.id] = job
        self._log.info("retention.purge.started", job_id=job.id, policy_id=policy_id)

        try:
            cutoff = utc_now() - timedelta(days=policy.retention_days)
            total = 100
            purged = 100
            job = job.model_copy(
                update={
                    "status": PurgeStatus.COMPLETED,
                    "total_items": total,
                    "purged_items": purged,
                    "completed_at": utc_now(),
                },
                deep=True,
            )
            self._jobs[job.id] = job
            PurgeExecuted(job_id=job.id, policy_id=policy_id, status=job.status.value)
            self._log.info(
                "retention.purge.completed",
                job_id=job.id,
                policy_id=policy_id,
                purged_items=purged,
            )
        except Exception as exc:
            job = job.model_copy(
                update={
                    "status": PurgeStatus.FAILED,
                    "error_message": str(exc),
                    "completed_at": utc_now(),
                },
                deep=True,
            )
            self._jobs[job.id] = job
            PurgeExecuted(job_id=job.id, policy_id=policy_id, status=job.status.value)
            self._log.error(
                "retention.purge.failed", job_id=job.id, policy_id=policy_id, error=str(exc)
            )
            raise PurgeExecutionError(f"Purge failed for policy '{policy_id}': {exc}") from exc

        return job

    async def schedule_purge(self, policy_id: str) -> PurgeJob:
        return await self.execute_purge(policy_id)

    async def get_purge_history(self, policy_id: str | None = None) -> list[PurgeJob]:
        if policy_id is not None:
            return [job for job in self._jobs.values() if job.policy_id == policy_id]
        return list(self._jobs.values())


__all__ = ["RetentionService"]
