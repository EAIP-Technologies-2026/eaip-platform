"""ApplicationHealthService — aggregated health reporting for the platform.

The :class:`ApplicationHealthService` provides a single entry point for
querying the health of the entire EAIP application:

* **Platform health** — delegating to the platform :class:`HealthReporter`.
* **Runtime health** — delegating to the runtime kernel diagnostics.
* **Module health** — individual health checks per registered module.
* **Plugin health** — individual health checks per registered plugin.
* **Startup diagnostics** — captured during the startup pipeline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import get_logger
from eaip.runtime.health import RuntimeHealthCheck
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.application.diagnostics import StartupDiagnostics
    from eaip.application.pipeline import StartupPipeline
    from eaip.platform.platform import Platform
    from eaip.runtime.kernel import RuntimeKernel


class ApplicationHealthService:
    """Aggregated health reporting for the EAIP application.

    Usage::

        health = ApplicationHealthService(platform, kernel, pipeline, diagnostics)
        overall = await health.report()
    """

    def __init__(
        self,
        platform: Platform,
        kernel: RuntimeKernel | None = None,
        pipeline: StartupPipeline | None = None,
        diagnostics: StartupDiagnostics | None = None,
    ) -> None:
        """Initialize the health service with platform and optional components."""
        self._platform = platform
        self._kernel = kernel
        self._pipeline = pipeline
        self._diagnostics = diagnostics
        self._log = get_logger("eaip.application.health")

    # ------------------------------------------------------------------
    # Individual health checks
    # ------------------------------------------------------------------

    async def platform_health(self) -> HealthReport:
        """Return the platform-level health rollup.

        Delegates to :meth:`eaip.health.reporter.HealthReporter.report`.
        """
        try:
            return await self._platform.health.report()
        except BaseException as exc:
            self._log.error("health.platform.check_failed", error=repr(exc))
            return HealthReport(
                component="platform",
                status=HealthStatus.UNHEALTHY,
                message=f"platform health check raised: {exc!r}",
                observed_at=utc_now(),
            )

    async def runtime_health(self) -> HealthReport:
        """Return runtime kernel health.

        Checks that the kernel is running and its diagnostics are healthy.
        """
        if self._kernel is None:
            return HealthReport(
                component="runtime",
                status=HealthStatus.DEGRADED,
                message="runtime kernel not configured",
                observed_at=utc_now(),
            )
        try:
            if not self._kernel.is_running:
                return HealthReport(
                    component="runtime",
                    status=HealthStatus.DEGRADED,
                    message="runtime kernel not running",
                    observed_at=utc_now(),
                )
            module_count = len(self._kernel.registry.module_names())
            return HealthReport(
                component="runtime",
                status=HealthStatus.HEALTHY,
                message=f"runtime kernel running with {module_count} module(s)",
                details={"module_count": module_count, "is_running": self._kernel.is_running},
                observed_at=utc_now(),
            )
        except BaseException as exc:
            return HealthReport(
                component="runtime",
                status=HealthStatus.UNHEALTHY,
                message=f"runtime health check raised: {exc!r}",
                observed_at=utc_now(),
            )

    async def module_health(self, module_name: str | None = None) -> list[HealthReport]:
        """Return health reports for registered modules.

        Args:
            module_name: If set, only return health for the named module.

        Returns:
            A list of health reports, one per matching module.
        """
        if self._kernel is None:
            return [
                HealthReport(
                    component="modules",
                    status=HealthStatus.DEGRADED,
                    message="runtime kernel not configured",
                    observed_at=utc_now(),
                )
            ]

        results: list[HealthReport] = []
        for name in self._kernel.registry.module_names():
            if module_name is not None and name != module_name:
                continue
            module = self._kernel.host.get_module(name)
            if module is None:
                results.append(
                    HealthReport(
                        component=name,
                        status=HealthStatus.UNHEALTHY,
                        message="module not found in host",
                        observed_at=utc_now(),
                    )
                )
                continue
            try:
                check = RuntimeHealthCheck(name=name, module=module)
                report = await check.check()
                results.append(report)
            except BaseException as exc:
                results.append(
                    HealthReport(
                        component=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"module health check raised: {exc!r}",
                        observed_at=utc_now(),
                    )
                )
        return results

    async def plugin_health(self) -> list[HealthReport]:
        """Return health reports for registered plugins."""
        results: list[HealthReport] = []
        try:
            results.extend(
                HealthReport(
                    component=f"plugin:{plugin.manifest.name}",
                    status=HealthStatus.HEALTHY,
                    message="plugin registered",
                    details={"version": plugin.manifest.version},
                    observed_at=utc_now(),
                )
                for plugin in self._platform.plugins.all()
            )
        except BaseException as exc:
            results.append(
                HealthReport(
                    component="plugins",
                    status=HealthStatus.UNHEALTHY,
                    message=f"plugin health check raised: {exc!r}",
                    observed_at=utc_now(),
                )
            )
        return results

    async def startup_diagnostics(self) -> HealthReport:
        """Return startup diagnostics as a health report."""
        if self._diagnostics is None:
            return HealthReport(
                component="startup",
                status=HealthStatus.DEGRADED,
                message="startup diagnostics not configured",
                observed_at=utc_now(),
            )
        try:
            report = self._diagnostics.report(
                pipeline=self._pipeline,
                platform=self._platform,
                kernel=self._kernel,
            )
            status = HealthStatus.HEALTHY
            if report.errors:
                status = HealthStatus.DEGRADED
            return HealthReport(
                component="startup",
                status=status,
                message=f"startup completed in {report.startup_duration_seconds:.3f}s",
                details={
                    "startup_duration_seconds": report.startup_duration_seconds,
                    "phase": report.phase,
                    "module_count": report.module_count,
                    "plugin_count": report.plugin_count,
                    "config_validated": report.config_validated,
                    "runtime_version": report.runtime_version,
                    "error_count": len(report.errors),
                },
                observed_at=utc_now(),
            )
        except BaseException as exc:
            return HealthReport(
                component="startup",
                status=HealthStatus.UNHEALTHY,
                message=f"startup diagnostics raised: {exc!r}",
                observed_at=utc_now(),
            )

    # ------------------------------------------------------------------
    # Aggregated report
    # ------------------------------------------------------------------

    async def report(self) -> HealthReport:
        """Produce a single aggregated health report for the entire application.

        Combines platform health, runtime health, module health, plugin health,
        and startup diagnostics into one rollup.
        """
        children: list[HealthReport] = []

        children.append(await self.platform_health())

        runtime = await self.runtime_health()
        children.append(runtime)

        modules = await self.module_health()
        if modules:
            children.extend(modules)

        plugins = await self.plugin_health()
        if plugins:
            children.extend(plugins)

        children.append(await self.startup_diagnostics())

        if not children:
            return HealthReport(
                component="application",
                status=HealthStatus.HEALTHY,
                message="no health sources configured",
                observed_at=utc_now(),
            )

        worst = max((c.status for c in children), key=lambda s: s.numeric)
        message = {
            HealthStatus.HEALTHY: "application healthy",
            HealthStatus.DEGRADED: "application degraded",
            HealthStatus.UNHEALTHY: "application unhealthy",
        }[worst]

        return HealthReport(
            component="application",
            status=worst,
            message=message,
            children=tuple(children),
            observed_at=utc_now(),
        )


__all__ = ["ApplicationHealthService"]
