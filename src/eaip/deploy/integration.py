"""Runtime module integration for deployment & release management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.deploy.deployer import Deployer
from eaip.deploy.environment import EnvironmentManager
from eaip.deploy.health import DeployHealthCheck
from eaip.deploy.release_manager import ReleaseManager
from eaip.deploy.rollback import RollbackManager
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DeployRuntimeModule:
    """Runtime module that registers the deploy capability and health check."""

    name: str = "deploy"

    def __init__(
        self,
        release_manager: ReleaseManager | None = None,
        deployer: Deployer | None = None,
        rollback_manager: RollbackManager | None = None,
        environment_manager: EnvironmentManager | None = None,
    ) -> None:
        """Initialize the runtime module with optional component instances."""
        self._release_manager = release_manager or ReleaseManager()
        self._deployer = deployer or Deployer()
        self._rollback_manager = rollback_manager or RollbackManager()
        self._environment_manager = environment_manager or EnvironmentManager()
        self._log = get_logger("eaip.deploy.integration")

    @property
    def release_manager(self) -> ReleaseManager:
        """Return the release manager instance."""
        return self._release_manager

    @property
    def deployer(self) -> Deployer:
        """Return the deployer instance."""
        return self._deployer

    @property
    def rollback_manager(self) -> RollbackManager:
        """Return the rollback manager instance."""
        return self._rollback_manager

    @property
    def environment_manager(self) -> EnvironmentManager:
        """Return the environment manager instance."""
        return self._environment_manager

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the deploy capability and health check with the kernel.

        Args:
            kernel: The runtime kernel to register with.
        """
        self._log.info("deploy.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.deploy",
            title="Deployment & Release Management",
            description="Managed release lifecycle, deployment strategies, and rollback support",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("deploy", "release", "rollback", "environment"),
        )
        platform.capabilities.register(capability)
        platform.health.register(DeployHealthCheck())
        self._log.info("deploy.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:  # noqa: ARG002
        """Shut down the deploy module."""
        self._log.info("deploy.module.stopping")


__all__ = ["DeployRuntimeModule"]
