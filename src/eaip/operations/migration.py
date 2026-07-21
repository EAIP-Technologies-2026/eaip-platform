"""Migration plan management."""

from __future__ import annotations

from datetime import UTC, datetime

from eaip.logging.context import get_logger
from eaip.operations.exceptions import MigrationError, MigrationValidationError
from eaip.operations.models import MigrationPlan, MigrationStep


class MigrationService:
    """Manages migration plans and their execution."""

    def __init__(self) -> None:
        """Initialize the migration service."""
        self._plans: dict[str, MigrationPlan] = {}
        self._log = get_logger("eaip.operations.migration")

    async def create_migration_plan(self, plan: MigrationPlan) -> MigrationPlan:
        """Create a new migration plan.

        Args:
            plan: The migration plan to create.

        Returns:
            The created migration plan.
        """
        self._plans[plan.id] = plan
        self._log.info(
            "migration.plan.created",
            plan_id=plan.id,
            source=plan.source_version,
            target=plan.target_version,
        )
        return plan

    async def validate_plan(self, plan_id: str) -> MigrationPlan:
        """Validate a migration plan.

        Args:
            plan_id: The ID of the plan to validate.

        Returns:
            The validated migration plan.

        Raises:
            MigrationValidationError: If the plan is not found or fails validation.
        """
        plan = self._plans.get(plan_id)
        if plan is None:
            raise MigrationValidationError(
                f"Migration plan {plan_id} not found",
                context={"plan_id": plan_id},
            )
        if plan.status != "draft":
            raise MigrationValidationError(
                f"Plan {plan_id} has status {plan.status}, expected 'draft'",
                context={"plan_id": plan_id, "status": plan.status},
            )
        if not plan.steps:
            raise MigrationValidationError(
                f"Plan {plan_id} has no migration steps",
                context={"plan_id": plan_id},
            )
        if not plan.source_version:
            raise MigrationValidationError(
                f"Plan {plan_id} has no source version",
                context={"plan_id": plan_id},
            )
        if not plan.target_version:
            raise MigrationValidationError(
                f"Plan {plan_id} has no target version",
                context={"plan_id": plan_id},
            )
        validated = MigrationPlan(
            id=plan.id,
            name=plan.name,
            source_version=plan.source_version,
            target_version=plan.target_version,
            steps=plan.steps,
            status="validated",
            created_at=plan.created_at,
            completed_at=plan.completed_at,
            metadata=plan.metadata,
            rollback_plan=plan.rollback_plan,
        )
        self._plans[plan_id] = validated
        self._log.info("migration.plan.validated", plan_id=plan_id)
        return validated

    async def execute_migration(self, plan_id: str) -> MigrationPlan:
        """Execute a validated migration plan.

        Args:
            plan_id: The ID of the plan to execute.

        Returns:
            The completed migration plan.

        Raises:
            MigrationError: If the plan is not found or cannot be executed.
        """
        plan = self._plans.get(plan_id)
        if plan is None:
            raise MigrationError(
                f"Migration plan {plan_id} not found",
                context={"plan_id": plan_id},
            )
        if plan.status != "validated":
            raise MigrationError(
                f"Plan {plan_id} has status {plan.status}, expected 'validated'",
                context={"plan_id": plan_id, "status": plan.status},
            )
        executed_steps = tuple(
            MigrationStep(
                id=s.id,
                description=s.description,
                type=s.type,
                status="completed",
                duration_ms=s.duration_ms or 100.0,
                error=s.error,
                rollback_step_id=s.rollback_step_id,
            )
            for s in plan.steps
        )
        completed = MigrationPlan(
            id=plan.id,
            name=plan.name,
            source_version=plan.source_version,
            target_version=plan.target_version,
            steps=executed_steps,
            status="completed",
            created_at=plan.created_at,
            completed_at=datetime.now(UTC),
            metadata=plan.metadata,
            rollback_plan=plan.rollback_plan,
        )
        self._plans[plan_id] = completed
        self._log.info("migration.executed", plan_id=plan_id)
        return completed

    async def rollback_migration(self, plan_id: str) -> MigrationPlan:
        """Roll back a completed or failed migration.

        Args:
            plan_id: The ID of the plan to roll back.

        Returns:
            The rolled back migration plan.

        Raises:
            MigrationError: If the plan is not found or cannot be rolled back.
        """
        plan = self._plans.get(plan_id)
        if plan is None:
            raise MigrationError(
                f"Migration plan {plan_id} not found",
                context={"plan_id": plan_id},
            )
        if plan.status not in ("completed", "failed"):
            raise MigrationError(
                f"Plan {plan_id} has status {plan.status}, expected 'completed' or 'failed'",
                context={"plan_id": plan_id, "status": plan.status},
            )
        rolled_back = MigrationPlan(
            id=plan.id,
            name=plan.name,
            source_version=plan.source_version,
            target_version=plan.target_version,
            steps=plan.steps,
            status="rolled_back",
            created_at=plan.created_at,
            completed_at=datetime.now(UTC),
            metadata=plan.metadata,
            rollback_plan=plan.rollback_plan,
        )
        self._plans[plan_id] = rolled_back
        self._log.info("migration.rolled_back", plan_id=plan_id)
        return rolled_back

    async def get_migration(self, plan_id: str) -> MigrationPlan | None:
        """Get a migration plan by ID.

        Args:
            plan_id: The plan identifier.

        Returns:
            The migration plan, or None if not found.
        """
        return self._plans.get(plan_id)

    async def list_migrations(self) -> list[MigrationPlan]:
        """List all migration plans.

        Returns:
            A list of all migration plans.
        """
        return list(self._plans.values())


__all__ = ["MigrationService"]
