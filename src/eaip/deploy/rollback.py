"""Rollback management — create and execute rollback plans."""

from __future__ import annotations

from eaip.deploy.exceptions import RollbackFailedError
from eaip.deploy.models import RollbackPlan


class RollbackManager:
    """Creates and executes rollback plans for failed deployments."""

    def __init__(self) -> None:
        """Initialize the rollback manager with an empty plan store."""
        self._plans: dict[str, RollbackPlan] = {}

    def create_rollback_plan(
        self,
        plan_id: str,
        deployment_id: str,
        reason: str,
        steps: tuple[str, ...] = (),
    ) -> RollbackPlan:
        """Create a new rollback plan.

        Args:
            plan_id: Unique identifier for the rollback plan.
            deployment_id: Identifier of the deployment to roll back.
            reason: Human-readable reason for the rollback.
            steps: Ordered sequence of rollback steps.

        Returns:
            The newly created RollbackPlan.
        """
        plan = RollbackPlan(
            plan_id=plan_id,
            deployment_id=deployment_id,
            reason=reason,
            steps=steps,
        )
        self._plans[plan_id] = plan
        return plan

    def get_rollback_plan(self, plan_id: str) -> RollbackPlan | None:
        """Retrieve a rollback plan by its identifier.

        Args:
            plan_id: Unique identifier for the rollback plan.

        Returns:
            The RollbackPlan if found, or None.
        """
        return self._plans.get(plan_id)

    def execute_rollback(self, plan_id: str) -> RollbackPlan:
        """Execute a rollback plan.

        Validates that the plan exists and has at least one step.

        Args:
            plan_id: Unique identifier for the rollback plan.

        Returns:
            The executed RollbackPlan.

        Raises:
            RollbackFailedError: If the plan is not found or has no steps.
        """
        plan = self._plans.get(plan_id)
        if plan is None:
            msg = f"rollback plan not found: {plan_id!r}"
            raise RollbackFailedError(plan_id, msg)
        if not plan.steps:
            msg = f"rollback plan {plan_id!r} has no steps"
            raise RollbackFailedError(plan_id, msg)
        return plan

    @property
    def plans(self) -> dict[str, RollbackPlan]:
        """Return a copy of all tracked rollback plans."""
        return dict(self._plans)


__all__ = ["RollbackManager"]
