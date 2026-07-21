"""Deployment execution — strategy support, health check verification."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from eaip.deploy.exceptions import DeploymentFailedError
from eaip.deploy.models import Deployment, DeploymentConfig, DeploymentLog
from eaip.shared.time import utc_now


class Deployer:
    """Executes deployment plans with strategy support and health check verification."""

    def __init__(self) -> None:
        """Initialize the deployer with an empty deployment store and strategy registry."""
        self._deployments: dict[str, Deployment] = {}
        self._strategies: dict[str, Callable[..., None]] = {
            "rolling": self._rolling_deploy,
            "blue-green": self._blue_green_deploy,
            "canary": self._canary_deploy,
            "recreate": self._recreate_deploy,
        }

    def create_deployment(
        self,
        deployment_id: str,
        release_id: str,
        environment: str,
        config: DeploymentConfig,
    ) -> Deployment:
        """Create a new pending deployment.

        Args:
            deployment_id: Unique identifier for the deployment.
            release_id: Identifier of the release to deploy.
            environment: Target environment name.
            config: Deployment configuration including strategy.

        Returns:
            The newly created Deployment with status ``pending``.
        """
        deployment = Deployment(
            deployment_id=deployment_id,
            release_id=release_id,
            environment=environment,
            strategy=config.strategy,
            status="pending",
            config=config,
        )
        self._deployments[deployment_id] = deployment
        return deployment

    def get_deployment(self, deployment_id: str) -> Deployment | None:
        """Retrieve a deployment by its identifier.

        Args:
            deployment_id: Unique identifier for the deployment.

        Returns:
            The Deployment if found, or None.
        """
        return self._deployments.get(deployment_id)

    def execute_deployment(
        self,
        deployment_id: str,
        health_check: Callable[[], bool] | None = None,
    ) -> Deployment:
        """Execute a deployment with an optional health check callback.

        The deployment transitions through ``in_progress`` and then either
        ``completed`` or ``failed`` depending on strategy execution and health
        check result.

        Args:
            deployment_id: Unique identifier for the deployment.
            health_check: Optional callable returning True if healthy.

        Returns:
            The completed Deployment.

        Raises:
            DeploymentFailedError: If the deployment or health check fails.
        """
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            msg = f"deployment not found: {deployment_id!r}"
            raise DeploymentFailedError(deployment_id, msg)

        started = Deployment(
            deployment_id=deployment.deployment_id,
            release_id=deployment.release_id,
            environment=deployment.environment,
            strategy=deployment.strategy,
            status="in_progress",
            started_at=utc_now(),
            completed_at=None,
            log=deployment.log,
            config=deployment.config,
        )
        self._deployments[deployment_id] = started

        try:
            strategy_fn = self._strategies.get(deployment.strategy)
            if strategy_fn is None:
                msg = f"unsupported strategy: {deployment.strategy}"
                raise DeploymentFailedError(deployment_id, msg)
            strategy_fn(deployment)

            if health_check is not None and not health_check():
                msg = "health check failed after deployment"
                raise DeploymentFailedError(deployment_id, msg)

            completed = Deployment(
                deployment_id=deployment.deployment_id,
                release_id=deployment.release_id,
                environment=deployment.environment,
                strategy=deployment.strategy,
                status="completed",
                started_at=started.started_at,
                completed_at=utc_now(),
                log=deployment.log,
                config=deployment.config,
            )
            self._deployments[deployment_id] = completed
            return completed
        except DeploymentFailedError:
            failed = Deployment(
                deployment_id=deployment.deployment_id,
                release_id=deployment.release_id,
                environment=deployment.environment,
                strategy=deployment.strategy,
                status="failed",
                started_at=started.started_at,
                completed_at=utc_now(),
                log=deployment.log,
                config=deployment.config,
            )
            self._deployments[deployment_id] = failed
            raise

    def add_log(
        self,
        deployment_id: str,
        level: str,
        message: str,
        component: str,
    ) -> Deployment | None:
        """Append a log entry to an existing deployment.

        Args:
            deployment_id: Unique identifier for the deployment.
            level: Log severity (info, warn, error).
            message: Log message text.
            component: Component that generated the log entry.

        Returns:
            The updated Deployment, or None if not found.
        """
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            return None
        log_entry = DeploymentLog(
            level=level,
            message=message,
            component=component,
        )
        updated = Deployment(
            deployment_id=deployment.deployment_id,
            release_id=deployment.release_id,
            environment=deployment.environment,
            strategy=deployment.strategy,
            status=deployment.status,
            started_at=deployment.started_at,
            completed_at=deployment.completed_at,
            log=(*deployment.log, log_entry),
            config=deployment.config,
        )
        self._deployments[deployment_id] = updated
        return updated

    def _rolling_deploy(self, deployment: Deployment) -> None:
        pass

    def _blue_green_deploy(self, deployment: Deployment) -> None:
        pass

    def _canary_deploy(self, deployment: Deployment) -> None:
        pass

    def _recreate_deploy(self, deployment: Deployment) -> None:
        pass

    @property
    def deployments(self) -> dict[str, Deployment]:
        """Return a copy of all tracked deployments."""
        return dict(self._deployments)

    @property
    def strategies(self) -> dict[str, Callable[..., Any]]:
        """Return a copy of registered deployment strategies."""
        return dict(self._strategies)


__all__ = ["Deployer"]
