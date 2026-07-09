"""Runtime integration — PolicyRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.policy.authorization import AuthorizationManager
from eaip.policy.engine import PolicyEngine
from eaip.policy.health import PolicyHealthCheck
from eaip.policy.registry import PolicyRegistry

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class PolicyRuntimeModule:
    """RuntimeModule that manages policy during kernel boot.

    - On start: initialises the policy engine and registry,
      registers the policy health check.
    - On stop: disables all policies.
    """

    name: str = "policy"

    def __init__(
        self,
        engine: PolicyEngine | None = None,
        registry: PolicyRegistry | None = None,
    ) -> None:
        """Initialize the PolicyRuntimeModule.

        Args:
            engine: Optional policy engine. Creates a new one if not provided.
            registry: Optional policy registry. Creates a new one if not provided.
        """
        self._engine = engine or PolicyEngine()
        self._registry = registry or PolicyRegistry()
        self._authorization: AuthorizationManager | None = None
        self._log = get_logger("eaip.runtime.policy_integration")
        self._startup_duration: float = 0.0

    @property
    def startup_duration(self) -> float:
        """Return the last policy startup duration in seconds."""
        return self._startup_duration

    @property
    def engine(self) -> PolicyEngine:
        """Return the policy engine."""
        return self._engine

    @property
    def registry(self) -> PolicyRegistry:
        """Return the policy registry."""
        return self._registry

    @property
    def authorization(self) -> AuthorizationManager:
        """Return the AuthorizationManager, raising if not yet started."""
        if self._authorization is None:
            raise RuntimeError(
                "AuthorizationManager not available until start() is called"
            )
        return self._authorization

    async def start(self, kernel: RuntimeKernel) -> None:
        """Initialise the policy subsystem.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("policy.module.start")
        t0 = time.monotonic()

        self._authorization = AuthorizationManager(
            engine=self._engine,
            registry=self._registry,
            event_bus=kernel.platform.events if hasattr(kernel.platform, "events") else None,
        )

        check = PolicyHealthCheck(self._registry)
        kernel.platform.health.register(check)

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "policy.module.complete",
            policies=len(self._registry),
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Disable all policies during shutdown.

        Args:
            _kernel: The runtime kernel.
        """
        self._log.info("policy.module.stop")
        for policy in self._registry.all():
            if policy.enabled:
                updated = policy.model_copy(
                    update={"enabled": False, "metadata": {**policy.metadata}}
                )
                self._registry.register(updated, replace=True)
        self._log.info("policy.module.stopped")


__all__ = ["PolicyRuntimeModule"]
