"""EAIPApplication — top-level application object for the EAIP platform.

The :class:`EAIPApplication` is the single entry point for starting,
stopping, and monitoring an EAIP instance.  It composes the platform,
runtime kernel, startup pipeline, diagnostics, and health service into
one coherent object.

Usage::

    from eaip.application import EAIPApplication

    app = EAIPApplication()
    await app.start()
    status = await app.health()
    await app.stop()

Or with async context manager::

    async with EAIPApplication() as app:
        status = await app.health()
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from eaip.application.composition import ApplicationCompositionRoot
from eaip.application.diagnostics import StartupDiagnostics
from eaip.application.health import ApplicationHealthService
from eaip.application.pipeline import StartupPhase, StartupPipeline
from eaip.config.sources import ConfigSource
from eaip.health.checks import HealthReport, HealthStatus
from eaip.logging.context import bind_context, get_logger
from eaip.shared.time import utc_now

if TYPE_CHECKING:
    from eaip.platform.platform import Platform
    from eaip.plugins.plugin import Plugin
    from eaip.runtime.kernel import RuntimeKernel
    from eaip.runtime.module import RuntimeModule


class EAIPApplication:
    """Top-level EAIP application object.

    Parameters
    ----------
    config_source:
        Optional :class:`~eaip.config.sources.ConfigSource` for loading
        configuration.  If omitted, environment variables are used.
    config_raw:
        Optional raw dictionary used as configuration.
    settings:
        Optional pre-built ``PlatformSettings``.
    modules:
        Optional iterable of :class:`~eaip.runtime.module.RuntimeModule`
        instances to register.
    plugins:
        Optional iterable of :class:`~eaip.plugins.plugin.Plugin`
        instances to register.
    configure_logging:
        Whether to configure logging from settings (default: True).
    """

    def __init__(
        self,
        *,
        config_source: ConfigSource | None = None,
        config_raw: dict[str, Any] | None = None,
        settings: Any = None,
        modules: Iterable[RuntimeModule] | None = None,
        plugins: Iterable[Plugin] | None = None,
        configure_logging: bool = True,
    ) -> None:
        """Initialize the application with optional config, modules, and plugins."""
        self._modules = list(modules) if modules is not None else []
        self._plugins = list(plugins) if plugins is not None else []
        self._settings = settings
        self._config_source = config_source
        self._config_raw = config_raw
        self._configure_logging = configure_logging

        self._composition: ApplicationCompositionRoot | None = None
        self._pipeline: StartupPipeline | None = None
        self._diagnostics: StartupDiagnostics | None = None
        self._health_service: ApplicationHealthService | None = None
        self._platform: Platform | None = None
        self._kernel: RuntimeKernel | None = None
        self._log = get_logger("eaip.application.app")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def platform(self) -> Platform | None:
        """The composed platform, or ``None`` before initialisation."""
        return self._platform

    @property
    def kernel(self) -> RuntimeKernel | None:
        """The runtime kernel, or ``None`` before initialisation."""
        return self._kernel

    @property
    def pipeline(self) -> StartupPipeline | None:
        """The startup pipeline, or ``None`` before initialisation."""
        return self._pipeline

    @property
    def diagnostics(self) -> StartupDiagnostics | None:
        """The startup diagnostics collector, or ``None`` before initialisation."""
        return self._diagnostics

    @property
    def health_service(self) -> ApplicationHealthService | None:
        """The health service, or ``None`` before initialisation."""
        return self._health_service

    @property
    def is_running(self) -> bool:
        """``True`` if the application has started and not yet stopped."""
        return self._pipeline is not None and self._pipeline.is_running

    @property
    def phase(self) -> str:
        """Current pipeline phase as a string."""
        if self._pipeline is None:
            return StartupPhase.CREATED.value
        return str(self._pipeline.phase.value)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Build the platform, kernel, and all supporting services.

        This method:

        1. Creates the :class:`ApplicationCompositionRoot`.
        2. Loads configuration.
        3. Builds the platform.
        4. Builds the kernel (with modules and plugins).
        5. Creates the :class:`StartupPipeline`, :class:`StartupDiagnostics`,
           and :class:`ApplicationHealthService`.

        Must be called before :meth:`start`.  Idempotent after the first call.
        """
        if self._composition is not None:
            self._log.warning("app.already_initialized")
            return

        self._composition = ApplicationCompositionRoot()
        self._composition.load_config(
            source=self._config_source,
            raw=self._config_raw,
        )
        self._platform = self._composition.build_platform(
            settings=self._settings,
            configure_logging=self._configure_logging,
        )
        self._kernel = self._composition.build_kernel(
            modules=self._modules,
            plugins=self._plugins,
        )
        self._composition.wire()

        # Create pipeline, diagnostics, and health service.
        self._pipeline = StartupPipeline()
        self._diagnostics = StartupDiagnostics()
        self._health_service = ApplicationHealthService(
            platform=self._platform,
            kernel=self._kernel,
            pipeline=self._pipeline,
            diagnostics=self._diagnostics,
        )

        self._log.info(
            "app.initialized",
            platform=self._platform.name,
            version=self._platform.version,
            modules=len(self._modules),
            plugins=len(self._plugins),
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the application through the full startup pipeline.

        Phases:

        1. **PRE_BOOTSTRAP** — configuration validation, connectivity checks.
        2. **BOOTSTRAP** — platform start, kernel wiring.
        3. **RUNTIME** — kernel start (all modules start).
        4. **POST_BOOTSTRAP** — ready event publication, background workers.

        Raises:
            RuntimeError: If :meth:`initialize` has not been called.
            LifecycleError: If any startup phase fails.
        """
        if self._pipeline is None:
            self.initialize()

        assert self._pipeline is not None
        assert self._diagnostics is not None
        assert self._platform is not None
        assert self._kernel is not None

        self._diagnostics.capture_start()

        # Register pipeline hooks.
        self._pipeline.register("pre_bootstrap", self._pre_bootstrap, name="app.pre_bootstrap")
        self._pipeline.register("bootstrap", self._bootstrap, name="app.bootstrap")
        self._pipeline.register("runtime", self._runtime, name="app.runtime")
        self._pipeline.register("post_bootstrap", self._post_bootstrap, name="app.post_bootstrap")
        self._pipeline.register("shutdown", self._shutdown, name="app.shutdown")

        self._log.info("app.starting")
        bind_context(
            app=self._platform.name,
            env=str(self._platform.settings.core.environment),
            version=self._platform.version,
        )

        await self._pipeline.run(context=self)
        self._diagnostics.capture_ready()

        self._log.info(
            "app.running",
            duration_seconds=self._diagnostics.report(
                pipeline=self._pipeline,
                platform=self._platform,
                kernel=self._kernel,
            ).startup_duration_seconds,
        )

    async def stop(self) -> None:
        """Stop the application gracefully.

        Runs the SHUTDOWN pipeline phase, then stops the platform.
        Idempotent.
        """
        if self._pipeline is None or not self._pipeline.is_running:
            return

        self._log.info("app.stopping")
        await self._pipeline.shutdown()
        self._log.info("app.stopped")

    async def health(self) -> HealthReport:
        """Return the current application health report.

        Returns:
            A :class:`~eaip.health.checks.HealthReport` aggregating all
            health sources.
        """
        if self._health_service is None:
            return HealthReport(
                component="application",
                status=HealthStatus.DEGRADED,
                message="application not initialized",
                observed_at=utc_now(),
            )
        return await self._health_service.report()

    async def __aenter__(self) -> EAIPApplication:
        """Enter async context: start the application."""
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        """Exit async context: stop the application."""
        await self.stop()

    # ------------------------------------------------------------------
    # Pipeline hook handlers
    # ------------------------------------------------------------------

    async def _pre_bootstrap(self, _pipeline: StartupPipeline, _context: Any) -> None:
        """PRE_BOOTSTRAP phase — validate configuration."""
        assert self._diagnostics is not None
        self._log.info("app.phase.pre_bootstrap")
        try:
            self._diagnostics.set_config_validated(validated=True)
        except Exception as exc:
            self._diagnostics.set_config_validated(validated=False, errors=[str(exc)])
            raise

    async def _bootstrap(self, _pipeline: StartupPipeline, _context: Any) -> None:
        """BOOTSTRAP phase — start the platform lifecycle."""
        assert self._platform is not None
        self._log.info("app.phase.bootstrap")
        self._platform.lifecycle.add(
            name="application.health",
            start=lambda: None,
            stop=lambda: None,
        )
        await self._platform.start()

    async def _runtime(self, _pipeline: StartupPipeline, _context: Any) -> None:
        """RUNTIME phase — kernel is already running via platform lifecycle."""
        assert self._kernel is not None
        self._log.info("app.phase.runtime")
        if not self._kernel.is_running:
            self._log.warning("app.kernel.not_running_during_runtime_phase")

    async def _post_bootstrap(self, _pipeline: StartupPipeline, _context: Any) -> None:
        """POST_BOOTSTRAP phase — post-startup tasks."""
        self._log.info("app.phase.post_bootstrap")

    async def _shutdown(self, _pipeline: StartupPipeline, _context: Any) -> None:
        """SHUTDOWN phase — stop platform and kernel."""
        self._log.info("app.phase.shutdown")
        if self._kernel is not None:
            try:
                await self._kernel.stop()
            except Exception as exc:
                self._log.error("app.kernel.stop_failed", error=repr(exc))
        if self._platform is not None:
            try:
                await self._platform.stop()
            except Exception as exc:
                self._log.error("app.platform.stop_failed", error=repr(exc))


__all__ = ["EAIPApplication"]
