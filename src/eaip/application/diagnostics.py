"""StartupDiagnostics — collects and reports application startup information.

The :class:`StartupDiagnostics` captures a snapshot of the platform state
at startup time, including:

* Startup duration (wall-clock time between start and ready).
* Registered modules and their dependencies.
* Registered plugins.
* Configuration validation status.
* Dependency graph summary.
* EAIP runtime version.
* Pipeline phase information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from eaip._version import __version__
from eaip.logging.context import get_logger
from eaip.runtime.graph import DependencyGraph
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.application.pipeline import StartupPipeline
    from eaip.platform.platform import Platform
    from eaip.runtime.kernel import RuntimeKernel


@dataclass(frozen=True, slots=True)
class StartupDiagnosticsReport:
    """Immutable snapshot of startup diagnostics.

    Attributes:
    ----------
    startup_duration_seconds:
        Wall-clock duration from pipeline start to ready (or current time).
    phase:
        Current pipeline phase.
    modules:
        Sorted list of registered module names.
    module_count:
        Number of registered modules.
    plugins:
        Sorted list of registered plugin names.
    plugin_count:
        Number of registered plugins.
    config_validated:
        Whether configuration was validated successfully.
    dependency_graph:
        Summary of module dependency relationships.
    runtime_version:
        EAIP version string.
    started_at:
        ISO-formatted timestamp of pipeline start.
    errors:
        List of error messages encountered during startup.
    """

    startup_duration_seconds: float = 0.0
    phase: str = "created"
    modules: list[str] = field(default_factory=list)
    module_count: int = 0
    plugins: list[str] = field(default_factory=list)
    plugin_count: int = 0
    config_validated: bool = True
    dependency_graph: dict[str, Any] = field(default_factory=dict)
    runtime_version: str = __version__
    started_at: str = ""
    errors: list[str] = field(default_factory=list)


class StartupDiagnostics:
    """Collects and reports application startup diagnostics.

    Usage::

        diagnostics = StartupDiagnostics()
        diagnostics.capture_start()
        # ... start platform ...
        diagnostics.capture_ready(platform, kernel)
        report = diagnostics.report()
    """

    def __init__(self) -> None:
        """Initialize the diagnostics collector with empty state."""
        self._started_at: datetime | None = None
        self._ready_at: datetime | None = None
        self._config_validated: bool = True
        self._config_errors: list[str] = []
        self._errors: list[str] = []
        self._log = get_logger("eaip.application.diagnostics")

    # ------------------------------------------------------------------
    # Capture methods
    # ------------------------------------------------------------------

    def capture_start(self) -> None:
        """Record the start time of the application."""
        self._started_at = utc_now()
        self._log.debug("diagnostics.start_captured")

    def capture_ready(self) -> None:
        """Record the ready time of the application."""
        self._ready_at = utc_now()
        self._log.debug("diagnostics.ready_captured")

    def set_config_validated(self, validated: bool, errors: list[str] | None = None) -> None:
        """Set whether configuration validation passed."""
        self._config_validated = validated
        if errors:
            self._config_errors = errors
            self._errors.extend(errors)

    def add_error(self, error: str) -> None:
        """Record a startup error."""
        self._errors.append(error)
        self._log.warning("diagnostics.error_recorded", error=error)

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def report(
        self,
        pipeline: StartupPipeline | None = None,
        platform: Platform | None = None,
        kernel: RuntimeKernel | None = None,
    ) -> StartupDiagnosticsReport:
        """Produce a :class:`StartupDiagnosticsReport` from captured state.

        Args:
            pipeline: The startup pipeline to read phase from.
            platform: The platform to read plugins from.
            kernel: The runtime kernel to read modules from.

        Returns:
            A frozen snapshot of diagnostic information.
        """
        now = utc_now()
        duration = 0.0
        started_str = ""

        if self._started_at is not None:
            end = self._ready_at or now
            duration = (end - self._started_at).total_seconds()
            started_str = self._started_at.isoformat()

        modules: list[str] = []
        if kernel is not None:
            modules = kernel.registry.module_names()

        plugins: list[str] = []
        if platform is not None:
            plugins = sorted(p.manifest.name for p in platform.plugins.all())

        dep_graph: dict[str, Any] = {}
        if kernel is not None and kernel.host.module_names:
            loader = kernel.host._loader
            all_modules = loader.all()
            if all_modules:
                graph = DependencyGraph(all_modules)
                ordered = graph.ordered()
                dep_graph = {
                    "module_count": len(ordered),
                    "startup_order": [m.name for m in ordered],
                }

        return StartupDiagnosticsReport(
            startup_duration_seconds=duration,
            phase=str(pipeline.phase.value) if pipeline is not None else "unknown",
            modules=modules,
            module_count=len(modules),
            plugins=plugins,
            plugin_count=len(plugins),
            config_validated=self._config_validated,
            dependency_graph=dep_graph,
            runtime_version=__version__,
            started_at=started_str,
            errors=list(self._errors),
        )


__all__ = [
    "StartupDiagnostics",
    "StartupDiagnosticsReport",
]
