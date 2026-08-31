"""Environment management — track current state and health status per environment."""

from __future__ import annotations

from eaip.deploy.exceptions import InvalidEnvironmentError
from eaip.deploy.models import EnvironmentStatus
from eaip.shared.time import utc_now


class EnvironmentManager:
    """Manages environments and tracks their current deployment state and health."""

    VALID_ENVIRONMENTS = ("dev", "staging", "prod")

    def __init__(self) -> None:
        """Initialize the environment manager with an empty environment store."""
        self._environments: dict[str, EnvironmentStatus] = {}

    def add_environment(
        self,
        environment: str,
        version: str = "",
        health_status: str = "healthy",
    ) -> EnvironmentStatus:
        """Register a new environment.

        Args:
            environment: Environment name (must be in VALID_ENVIRONMENTS).
            version: Initial version string.
            health_status: Initial health status.

        Returns:
            The newly created EnvironmentStatus.

        Raises:
            InvalidEnvironmentError: If the environment name is not valid.
        """
        if environment not in self.VALID_ENVIRONMENTS:
            raise InvalidEnvironmentError(environment)
        status = EnvironmentStatus(
            environment=environment,
            current_release_id="",
            health_status=health_status,
            version=version,
        )
        self._environments[environment] = status
        return status

    def get_environment(self, environment: str) -> EnvironmentStatus | None:
        """Retrieve the current status of an environment.

        Args:
            environment: Environment name.

        Returns:
            The EnvironmentStatus if found, or None.
        """
        return self._environments.get(environment)

    def update_deployment(
        self,
        environment: str,
        release_id: str,
        version: str,
        health_status: str = "healthy",
    ) -> EnvironmentStatus:
        """Record a new deployment for an environment.

        Args:
            environment: Environment name.
            release_id: Identifier of the deployed release.
            version: Version string of the deployed release.
            health_status: Post-deployment health status.

        Returns:
            The updated EnvironmentStatus.

        Raises:
            InvalidEnvironmentError: If the environment name is not valid.
        """
        if environment not in self.VALID_ENVIRONMENTS:
            raise InvalidEnvironmentError(environment)
        status = EnvironmentStatus(
            environment=environment,
            current_release_id=release_id,
            health_status=health_status,
            last_deployed_at=utc_now(),
            version=version,
        )
        self._environments[environment] = status
        return status

    def set_health_status(
        self,
        environment: str,
        health_status: str,
    ) -> EnvironmentStatus | None:
        """Update the health status of an environment.

        Args:
            environment: Environment name.
            health_status: New health status value.

        Returns:
            The updated EnvironmentStatus, or None if not found.
        """
        current = self._environments.get(environment)
        if current is None:
            return None
        status = EnvironmentStatus(
            environment=current.environment,
            current_release_id=current.current_release_id,
            health_status=health_status,
            last_deployed_at=current.last_deployed_at,
            version=current.version,
        )
        self._environments[environment] = status
        return status

    def get_health_summary(self) -> dict[str, str]:
        """Return a map of environment -> health_status for all environments."""
        return {env: status.health_status for env, status in self._environments.items()}

    @property
    def environments(self) -> dict[str, EnvironmentStatus]:
        """Return a copy of all tracked environment statuses."""
        return dict(self._environments)


__all__ = ["EnvironmentManager"]
