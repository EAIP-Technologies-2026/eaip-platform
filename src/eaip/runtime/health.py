"""Runtime health — module health checks and runtime diagnostics.

:class:`RuntimeHealthCheck` adapts a
:class:`~eaip.runtime.module.BaseRuntimeModule` to the
:class:`~eaip.health.checks.HealthCheck` protocol so that individual module
health is visible through the platform health rollup.

:class:`RuntimeDiagnostics` aggregates runtime component health (modules,
lifecycle state, hook registration) into a single diagnostic report.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.lifecycle.phases import LifecyclePhase
from eaip.shared.time import utc_now

if TYPE_CHECKING:  # pragma: no cover
    from eaip.lifecycle.manager import LifecycleManager
    from eaip.runtime.hooks import ObservabilityHooks
    from eaip.runtime.loader import ModuleLoader


@runtime_checkable
class _HasCheckHealth(Protocol):
    """Structural protocol for objects that expose ``check_health()``."""

    async def check_health(self) -> HealthReport: ...


class RuntimeHealthCheck:
    """Adapts a :class:`~eaip.runtime.module.BaseRuntimeModule` to :class:`HealthCheck`.

    This class satisfies the :class:`~eaip.health.checks.HealthCheck` protocol
    and can therefore be passed directly to
    :meth:`~eaip.health.reporter.HealthReporter.register`.
    """

    def __init__(self, name: str, module: Any) -> None:
        self.name = name
        self._module = module

    async def check(self) -> HealthReport:
        """Delegate to the module's ``check_health`` coroutine.

        If the module does not implement ``_HasCheckHealth``, a ``DEGRADED``
        report is returned so that the rollup surface can still show the
        module's presence.
        """
        if not isinstance(self._module, _HasCheckHealth):
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message="module does not expose health checks",
                observed_at=utc_now(),
            )
        try:
            return await self._module.check_health()
        except Exception as exc:
            return HealthReport(
                component=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"check_health raised: {exc!r}",
                observed_at=utc_now(),
            )


# Explicitly verify the class satisfies the HealthCheck protocol at import time.
assert isinstance(RuntimeHealthCheck("_", object()), HealthCheck)


class RuntimeDiagnostics:
    """Aggregate runtime component health into a single diagnostic report.

    Collects health from the module loader, lifecycle manager, and
    observability hooks to produce a comprehensive view of runtime health.

    Parameters
    ----------
    loader:
        The :class:`~eaip.runtime.loader.ModuleLoader` to inspect.
    lifecycle:
        The :class:`~eaip.lifecycle.manager.LifecycleManager` to inspect.
    hooks:
        The :class:`~eaip.runtime.hooks.ObservabilityHooks` to inspect.
    """

    def __init__(
        self,
        *,
        loader: ModuleLoader | None = None,
        lifecycle: LifecycleManager | None = None,
        hooks: ObservabilityHooks | None = None,
    ) -> None:
        self._loader = loader
        self._lifecycle = lifecycle
        self._hooks = hooks

    async def diagnose(self) -> HealthReport:
        """Run all available diagnostics and produce a rollup."""
        children: list[HealthReport] = []

        if self._lifecycle is not None:
            try:
                phase = self._lifecycle.phase
                phase_ok = phase in {
                    LifecyclePhase.RUNNING,
                    LifecyclePhase.STOPPED,
                    LifecyclePhase.CREATED,
                }
                children.append(
                    HealthReport(
                        component="lifecycle",
                        status=HealthStatus.HEALTHY if phase_ok else HealthStatus.DEGRADED,
                        message=f"phase={phase.value}",
                        observed_at=utc_now(),
                    )
                )
            except Exception as exc:
                children.append(
                    HealthReport(
                        component="lifecycle",
                        status=HealthStatus.UNHEALTHY,
                        message=f"lifecycle check failed: {exc!r}",
                        observed_at=utc_now(),
                    )
                )

        if self._loader is not None:
            try:
                names = self._loader.names()
                children.append(
                    HealthReport(
                        component="loader",
                        status=HealthStatus.HEALTHY,
                        message=f"modules registered: {len(names)}",
                        details={"modules": names},
                        observed_at=utc_now(),
                    )
                )
            except Exception as exc:
                children.append(
                    HealthReport(
                        component="loader",
                        status=HealthStatus.UNHEALTHY,
                        message=f"loader check failed: {exc!r}",
                        observed_at=utc_now(),
                    )
                )

        if self._hooks is not None:
            try:
                hook_names = sorted(self._hooks.registered_events())
                children.append(
                    HealthReport(
                        component="hooks",
                        status=HealthStatus.HEALTHY,
                        message=f"hook events registered: {len(hook_names)}",
                        details={"events": hook_names},
                        observed_at=utc_now(),
                    )
                )
            except Exception as exc:
                children.append(
                    HealthReport(
                        component="hooks",
                        status=HealthStatus.UNHEALTHY,
                        message=f"hooks check failed: {exc!r}",
                        observed_at=utc_now(),
                    )
                )

        if not children:
            return HealthReport(
                component="runtime.diagnostics",
                status=HealthStatus.HEALTHY,
                message="no diagnostic sources configured",
                observed_at=utc_now(),
            )

        worst = max((c.status for c in children), key=lambda s: s.numeric)
        return HealthReport(
            component="runtime.diagnostics",
            status=worst,
            message="runtime diagnostics complete",
            details={"component_count": len(children)},
            children=tuple(children),
            observed_at=utc_now(),
        )


__all__ = ["RuntimeDiagnostics", "RuntimeHealthCheck"]
