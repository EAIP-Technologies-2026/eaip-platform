"""Integration layer — wiring for the session subsystem."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.health.checks import HealthReport
from eaip.logging.context import get_logger
from eaip.session.context_manager import EnterpriseContextManager
from eaip.session.health import SessionHealthCheck
from eaip.session.lifecycle import SessionLifecycleManager
from eaip.session.manager import SessionManager
from eaip.session.models import SessionConfig
from eaip.session.serialization import SessionSerializer

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SessionRuntimeModule:
    """Runtime module for the session subsystem.

    Wires SessionManager, EnterpriseContextManager, SessionLifecycleManager,
    and SessionSerializer into the EAIP runtime, registering health
    checks and capabilities.
    """

    name: str = "session"

    def __init__(
        self,
        manager: SessionManager | None = None,
        context_manager: EnterpriseContextManager | None = None,
        lifecycle_manager: SessionLifecycleManager | None = None,
        serializer: SessionSerializer | None = None,
        **_kwargs: Any,
    ) -> None:
        """Initialize the SessionRuntimeModule.

        Args:
            manager: Optional SessionManager instance.
            context_manager: Optional EnterpriseContextManager instance.
            lifecycle_manager: Optional SessionLifecycleManager instance.
            serializer: Optional SessionSerializer instance.
        """
        self._manager = manager or SessionManager()
        self._context_manager = context_manager or EnterpriseContextManager()
        self._lifecycle_manager = lifecycle_manager or SessionLifecycleManager(
            manager=self._manager,
        )
        self._serializer = serializer or SessionSerializer()
        self._started = False
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.session.integration")

    @property
    def manager(self) -> SessionManager:
        """Return the SessionManager."""
        return self._manager

    @property
    def context_manager(self) -> EnterpriseContextManager:
        """Return the EnterpriseContextManager."""
        return self._context_manager

    @property
    def lifecycle_manager(self) -> SessionLifecycleManager:
        """Return the SessionLifecycleManager."""
        return self._lifecycle_manager

    @property
    def serializer(self) -> SessionSerializer:
        """Return the SessionSerializer."""
        return self._serializer

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel | None = None) -> None:
        """Start the session runtime module.

        Args:
            kernel: Optional runtime kernel for platform integration.
        """
        t0 = time.monotonic()
        self._log.info("integration.start")

        self._started = True

        if kernel is not None:
            kernel.platform.health.register(_SessionSystemHealthCheck(self._manager))
            kernel.platform.capabilities.register(self._capability())

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "integration.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        """Stop the session runtime module.

        Args:
            _kernel: Optional runtime kernel (unused).
        """
        self._log.info("integration.stop")
        self._started = False

    def _capability(self) -> Capability:
        """Create the capability descriptor for this module.

        Returns:
            A Capability instance.
        """
        return Capability(
            name="session:engine",
            title="Context & Session Intelligence",
            status=CapabilityStatus.ENABLED,
        )


class _SessionSystemHealthCheck:
    """Ad-hoc health check that wraps SessionHealthCheck for registration."""

    name: str = "session"

    def __init__(self, manager: SessionManager) -> None:
        """Initialize the health check.

        Args:
            manager: The SessionManager instance.
        """
        self._check = SessionHealthCheck(manager)

    async def check(self) -> HealthReport:
        """Delegate to SessionHealthCheck.check.

        Returns:
            A HealthReport.
        """
        return await self._check.check()


def create_session_integration(
    *,
    manager: SessionManager | None = None,
    context_manager: EnterpriseContextManager | None = None,
    lifecycle_manager: SessionLifecycleManager | None = None,
    serializer: SessionSerializer | None = None,
) -> SessionRuntimeModule:
    """Create a fully wired SessionRuntimeModule.

    Args:
        manager: Optional SessionManager.
        context_manager: Optional EnterpriseContextManager.
        lifecycle_manager: Optional SessionLifecycleManager.
        serializer: Optional SessionSerializer.

    Returns:
        A configured SessionRuntimeModule.
    """
    return SessionRuntimeModule(
        manager=manager,
        context_manager=context_manager,
        lifecycle_manager=lifecycle_manager,
        serializer=serializer,
    )


__all__ = [
    "SessionRuntimeModule",
    "create_session_integration",
]
