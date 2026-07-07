"""Abstract base for asynchronously-managed platform services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import final

from eaip.exceptions.domain import LifecycleError
from eaip.shared.identifiers import ComponentId


class ServiceState(StrEnum):
    """Finite state machine of a managed service.

    ::

        CREATED ──start──▶ STARTING ──▶ RUNNING ──stop──▶ STOPPING ──▶ STOPPED
                                          │                              │
                                          └────────── FAILED ◀───────────┘
    """

    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


_ALLOWED: dict[ServiceState, set[ServiceState]] = {
    ServiceState.CREATED: {ServiceState.STARTING, ServiceState.FAILED},
    ServiceState.STARTING: {ServiceState.RUNNING, ServiceState.FAILED},
    ServiceState.RUNNING: {ServiceState.STOPPING, ServiceState.FAILED},
    ServiceState.STOPPING: {ServiceState.STOPPED, ServiceState.FAILED},
    ServiceState.STOPPED: set(),
    ServiceState.FAILED: {ServiceState.STOPPING, ServiceState.STOPPED},
}


class AbstractService(ABC):
    """Base class for all long-lived platform services.

    Subclasses implement :meth:`_on_start` and :meth:`_on_stop`. The base
    class enforces the state machine and prevents illegal transitions.
    """

    __slots__ = ("_id", "_name", "_state")

    def __init__(self, *, name: str, component_id: ComponentId | None = None) -> None:
        """Initialize the service.

        Args:
            name: The name of the service.
            component_id: The unique identifier for the service.
        """
        if not name or not name.strip():
            raise ValueError("service name must be a non-empty string")
        self._id: ComponentId = component_id or ComponentId.new()
        self._name: str = name
        self._state: ServiceState = ServiceState.CREATED

    @property
    def id(self) -> ComponentId:
        """Return the unique identifier of the service."""
        return self._id

    @property
    def name(self) -> str:
        """Return the name of the service."""
        return self._name

    @property
    def state(self) -> ServiceState:
        """Return the current state of the service."""
        return self._state

    @final
    async def start(self) -> None:
        """Start the service, transitioning it to the RUNNING state."""
        self._transition(ServiceState.STARTING)
        try:
            await self._on_start()
        except BaseException:
            self._state = ServiceState.FAILED
            raise
        self._transition(ServiceState.RUNNING)

    @final
    async def stop(self) -> None:
        """Stop the service, transitioning it to the STOPPED state."""
        # Stopping is permitted from RUNNING or FAILED.
        if self._state not in {ServiceState.RUNNING, ServiceState.FAILED}:
            raise LifecycleError(
                f"cannot stop service in state {self._state}",
                context={"service": self._name, "state": str(self._state)},
            )
        self._state = ServiceState.STOPPING
        try:
            await self._on_stop()
        finally:
            self._state = ServiceState.STOPPED

    @abstractmethod
    async def _on_start(self) -> None:
        """Subclass hook performing the actual startup work."""

    @abstractmethod
    async def _on_stop(self) -> None:
        """Subclass hook performing the actual shutdown work."""

    def _transition(self, target: ServiceState) -> None:
        """Transition the service state.

        Args:
            target: The target state to transition to.

        Raises:
            LifecycleError: If the transition is illegal.
        """
        if target not in _ALLOWED[self._state]:
            raise LifecycleError(
                f"illegal state transition: {self._state} → {target}",
                context={
                    "service": self._name,
                    "from_state": str(self._state),
                    "to_state": str(target),
                },
            )
        self._state = target


__all__ = ["AbstractService", "ServiceState"]
