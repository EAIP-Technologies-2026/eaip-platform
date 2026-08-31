"""RollbackManager — record deployments, create plans, execute rollbacks."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.rollbackmgr.events import RollbackCompleted, RollbackFailed, RollbackStarted
from eaip.rollbackmgr.exceptions import DeploymentNotFoundError
from eaip.rollbackmgr.models import (
    Deployment,
    RollbackConfig,
    RollbackExecution,
    RollbackPlan,
)
from eaip.shared.time import utc_now


class RollbackManager:
    """Central service for managing deployments and rollback operations."""

    def __init__(self, config: RollbackConfig | None = None) -> None:
        self._config = config or RollbackConfig()
        self._deployments: dict[str, Deployment] = {}
        self._plans: dict[str, RollbackPlan] = {}
        self._executions: dict[str, RollbackExecution] = {}
        self._log = get_logger("eaip.rollbackmgr.service")

    @property
    def config(self) -> RollbackConfig:
        return self._config

    async def record_deployment(self, deployment: Deployment) -> Deployment:
        """Record a new deployment."""
        self._deployments[deployment.id] = deployment
        self._log.info("rollbackmgr.deployment.recorded", deployment_id=deployment.id)
        return deployment

    async def get_deployment(self, deployment_id: str) -> Deployment:
        """Get a deployment by ID."""
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            raise DeploymentNotFoundError(f"Deployment not found: {deployment_id}")
        return deployment

    async def list_deployments(self, environment: str | None = None) -> list[Deployment]:
        """List all deployments, optionally filtered by environment."""
        deployments = list(self._deployments.values())
        if environment is not None:
            deployments = [d for d in deployments if d.environment == environment]
        return deployments

    async def update_deployment(self, deployment_id: str, **changes: object) -> Deployment:
        """Update an existing deployment record."""
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            raise DeploymentNotFoundError(f"Deployment not found: {deployment_id}")
        updated = deployment.model_copy(update=changes)
        self._deployments[deployment_id] = updated
        self._log.info("rollbackmgr.deployment.updated", deployment_id=deployment_id)
        return updated

    async def create_plan(self, plan: RollbackPlan) -> RollbackPlan:
        """Create a rollback plan for a deployment."""
        deployment = self._deployments.get(plan.deployment_id)
        if deployment is None:
            raise DeploymentNotFoundError(f"Deployment not found: {plan.deployment_id}")
        self._plans[plan.id] = plan
        self._log.info(
            "rollbackmgr.plan.created", plan_id=plan.id, deployment_id=plan.deployment_id
        )
        return plan

    async def get_plan(self, plan_id: str) -> RollbackPlan:
        """Get a rollback plan by ID."""
        plan = self._plans.get(plan_id)
        if plan is None:
            raise DeploymentNotFoundError(f"Rollback plan not found: {plan_id}")
        return plan

    async def list_plans(self, deployment_id: str | None = None) -> list[RollbackPlan]:
        """List rollback plans, optionally filtered by deployment."""
        plans = list(self._plans.values())
        if deployment_id is not None:
            plans = [p for p in plans if p.deployment_id == deployment_id]
        return plans

    async def execute_rollback(self, plan_id: str, execution_id: str) -> RollbackExecution:
        """Execute a rollback plan."""
        plan = self._plans.get(plan_id)
        if plan is None:
            raise DeploymentNotFoundError(f"Rollback plan not found: {plan_id}")
        deployment = self._deployments.get(plan.deployment_id)
        if deployment is None:
            raise DeploymentNotFoundError(f"Deployment not found: {plan.deployment_id}")
        started = utc_now()
        RollbackStarted(
            execution_id=execution_id,
            deployment_id=plan.deployment_id,
            strategy=plan.strategy,
            started_at=started,
        )
        execution = RollbackExecution(
            id=execution_id,
            plan_id=plan_id,
            deployment_id=plan.deployment_id,
        )
        now = utc_now()
        delta = (now - started).total_seconds()
        completed = execution.model_copy(
            update={
                "success": True,
                "completed_at": now,
                "output": f"Rolled back deployment {deployment.name} (v{deployment.version})",
            }
        )
        self._executions[execution_id] = completed
        RollbackCompleted(
            execution_id=execution_id,
            deployment_id=plan.deployment_id,
            output=completed.output,
            duration_seconds=round(delta, 3),
        )
        updated_deployment = deployment.model_copy(update={"status": "rolled_back"})
        self._deployments[plan.deployment_id] = updated_deployment
        self._log.info(
            "rollbackmgr.rollback.completed",
            execution_id=execution_id,
            deployment_id=plan.deployment_id,
        )
        return completed

    async def fail_rollback(
        self,
        execution_id: str,
        plan_id: str,
        error_message: str = "",
    ) -> RollbackExecution:
        """Mark a rollback execution as failed."""
        plan = self._plans.get(plan_id)
        if plan is None:
            raise DeploymentNotFoundError(f"Rollback plan not found: {plan_id}")
        failed = RollbackExecution(
            id=execution_id,
            plan_id=plan_id,
            deployment_id=plan.deployment_id,
            completed_at=utc_now(),
            success=False,
            error_message=error_message,
        )
        self._executions[execution_id] = failed
        RollbackFailed(
            execution_id=execution_id,
            deployment_id=plan.deployment_id,
            error_message=error_message,
        )
        self._log.info(
            "rollbackmgr.rollback.failed",
            execution_id=execution_id,
            error=error_message,
        )
        return failed

    async def get_execution(self, execution_id: str) -> RollbackExecution:
        """Get a rollback execution by ID."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise DeploymentNotFoundError(f"Rollback execution not found: {execution_id}")
        return execution

    async def list_executions(self, deployment_id: str | None = None) -> list[RollbackExecution]:
        """List rollback executions, optionally filtered by deployment."""
        executions = list(self._executions.values())
        if deployment_id is not None:
            executions = [e for e in executions if e.deployment_id == deployment_id]
        return executions

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about deployments and rollbacks."""
        total_deployments = len(self._deployments)
        total_plans = len(self._plans)
        total_executions = len(self._executions)
        successful = sum(1 for e in self._executions.values() if e.success)
        failed = sum(1 for e in self._executions.values() if not e.success)
        return {
            "total_deployments": total_deployments,
            "total_plans": total_plans,
            "total_executions": total_executions,
            "successful_rollbacks": successful,
            "failed_rollbacks": failed,
        }


__all__ = ["RollbackManager"]
