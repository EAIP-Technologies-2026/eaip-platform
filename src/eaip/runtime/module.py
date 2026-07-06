"""RuntimeModule — the unit of runtime-kernel extension.

A :class:`RuntimeModule` is the fundamental building block of the Runtime
Kernel.  It is a self-describing, lifecycle-aware, health-reporting component
that the :class:`~eaip.runtime.host.RuntimeHost` discovers, orders, starts,
and stops.

Every module declares:

* A **name** (unique within the host).
* Zero or more **dependencies** (names of other modules that must start first).
* Optional **health check** support.

Relationship to Plugin
----------------------
Plugins (``eaip.plugins``) extend the *platform* from outside.  Modules extend
the *runtime kernel* from inside — they are first-party components managed by
the host directly.  Modules may register capabilities and plugins during
activation but are themselves not plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from eaip.health.checks import HealthReport, HealthStatus
from eaip.shared.time import utc_now

if TYPE_CHECKING:  # pragma: no cover
    from eaip.runtime.context import RuntimeContext
    from eaip.runtime.host import RuntimeHost


# ---------------------------------------------------------------------------
# Protocol — structural typing contract checked by ModuleLoader
# ---------------------------------------------------------------------------


@runtime_checkable
class RuntimeModule(Protocol):
    """Structural protocol that every runtime module must satisfy.

    Modules are discovered and loaded by :class:`~eaip.runtime.loader.ModuleLoader`.
    This protocol is intentionally minimal; extend it through
    :class:`BaseRuntimeModule` for full lifecycle and health support.
    """

    @property
    def name(self) -> str:
        """Unique, stable module name within the host (e.g. ``"eaip.telemetry"``)."""
        ...

    @property
    def dependencies(self) -> tuple[str, ...]:
        """Names of modules that must be started before this one."""
        ...

    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        """Called by the host during the startup phase."""
        ...

    async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        """Called by the host during the shutdown phase (LIFO order)."""
        ...


# ---------------------------------------------------------------------------
# Abstract base — convenience base class (not required but recommended)
# ---------------------------------------------------------------------------


class BaseRuntimeModule(ABC):
    """Convenience base class for runtime modules.

    Subclasses must implement :meth:`on_start`; :meth:`on_stop` defaults to a
    no-op so simple modules don't need shutdown logic.

    Health checks are opt-in: override :meth:`check_health` to expose liveness
    and readiness information to the platform health reporter.
    """

    # Subclasses may override these class attributes.
    module_name: str = ""
    module_dependencies: tuple[str, ...] = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

    # ------------------------------------------------------------------
    # RuntimeModule protocol fulfilment
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        if self.module_name:
            return self.module_name
        return type(self).__qualname__

    @property
    def dependencies(self) -> tuple[str, ...]:
        return self.module_dependencies

    @abstractmethod
    async def on_start(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        """Perform startup work.  Called exactly once by the host."""

    async def on_stop(self, host: RuntimeHost, ctx: RuntimeContext) -> None:
        """Perform shutdown work.  Default is a no-op."""

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def check_health(self) -> HealthReport:
        """Return a :class:`~eaip.health.HealthReport` for this module.

        The default implementation reports ``HEALTHY`` with the module name.
        Override to add real checks (e.g. connectivity probes).
        """
        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="module healthy",
            observed_at=utc_now(),
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, deps={self.dependencies!r})"


__all__ = ["BaseRuntimeModule", "RuntimeModule"]
