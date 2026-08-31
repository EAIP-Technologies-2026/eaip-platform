"""DocumentRedactionService — redact sensitive content in documents."""

from __future__ import annotations

from eaip.docredact.events import JobCreated, RedactionCompleted, RedactionFailed
from eaip.docredact.exceptions import RedactionError, RuleNotFoundError
from eaip.docredact.models import RedactionConfig, RedactionJob, RedactionJobStatus, RedactionRule
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class DocumentRedactionService:
    """Central service for applying redaction rules to documents."""

    def __init__(self, config: RedactionConfig | None = None) -> None:
        self._config = config or RedactionConfig()
        self._rules: dict[str, RedactionRule] = {}
        self._jobs: dict[str, RedactionJob] = {}
        self._log = get_logger("eaip.docredact.redactor")

    @property
    def config(self) -> RedactionConfig:
        return self._config

    async def create_rule(self, rule: RedactionRule) -> RedactionRule:
        """Create a new redaction rule."""
        self._rules[rule.id] = rule
        self._log.info("docredact.rule.created", rule_id=rule.id, name=rule.name)
        return rule

    async def get_rule(self, rule_id: str) -> RedactionRule:
        """Get a redaction rule by ID."""
        rule = self._rules.get(rule_id)
        if rule is None:
            raise RuleNotFoundError(f"Redaction rule not found: {rule_id}")
        return rule

    async def list_rules(self, enabled: bool | None = None) -> list[RedactionRule]:
        """List redaction rules, optionally filtered by enabled state."""
        result = list(self._rules.values())
        if enabled is not None:
            result = [r for r in result if r.enabled == enabled]
        return sorted(result, key=lambda r: r.name)

    async def create_job(self, job: RedactionJob) -> RedactionJob:
        """Create a new redaction job."""
        self._jobs[job.id] = job
        JobCreated(
            job_id=job.id,
            document_ref=job.document_ref,
            rules_count=len(job.rules_applied),
        )
        self._log.info("docredact.job.created", job_id=job.id, document_ref=job.document_ref)
        return job

    async def get_job(self, job_id: str) -> RedactionJob:
        """Get a redaction job by ID."""
        job = self._jobs.get(job_id)
        if job is None:
            raise RedactionError(f"Redaction job not found: {job_id}")
        return job

    async def list_jobs(self, status: RedactionJobStatus | None = None) -> list[RedactionJob]:
        """List redaction jobs, optionally filtered by status."""
        result = list(self._jobs.values())
        if status is not None:
            result = [j for j in result if j.status == status]
        return sorted(result, key=lambda j: j.id)

    async def run_job(self, job_id: str) -> RedactionJob:
        """Execute a redaction job by applying its rules."""
        job = self._jobs.get(job_id)
        if job is None:
            raise RedactionError(f"Redaction job not found: {job_id}")

        updated = job.model_copy(
            update={"status": RedactionJobStatus.RUNNING, "started_at": utc_now()}
        )
        self._jobs[job_id] = updated

        try:
            for rule_id in job.rules_applied:
                rule = self._rules.get(rule_id)
                if rule is None:
                    raise RuleNotFoundError(f"Redaction rule not found: {rule_id}")

            completed = updated.model_copy(
                update={"status": RedactionJobStatus.COMPLETED, "completed_at": utc_now()}
            )
            self._jobs[job_id] = completed

            RedactionCompleted(
                job_id=job_id,
                document_ref=job.document_ref,
                rules_applied=job.rules_applied,
            )
            self._log.info("docredact.job.completed", job_id=job_id)
            return completed

        except (RedactionError, RuleNotFoundError) as exc:
            failed = updated.model_copy(
                update={"status": RedactionJobStatus.FAILED, "completed_at": utc_now()}
            )
            self._jobs[job_id] = failed

            RedactionFailed(
                job_id=job_id,
                document_ref=job.document_ref,
                reason=str(exc),
            )
            self._log.error("docredact.job.failed", job_id=job_id, reason=str(exc))
            return failed

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about redaction rules and jobs."""
        return {
            "total_rules": len(self._rules),
            "enabled_rules": sum(1 for r in self._rules.values() if r.enabled),
            "total_jobs": len(self._jobs),
            "completed_jobs": sum(
                1 for j in self._jobs.values() if j.status == RedactionJobStatus.COMPLETED
            ),
            "failed_jobs": sum(
                1 for j in self._jobs.values() if j.status == RedactionJobStatus.FAILED
            ),
        }


__all__ = ["DocumentRedactionService"]
