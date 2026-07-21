"""Fluent builder for constructing a fully-wired EAIP application."""

from __future__ import annotations

from collections.abc import Callable
from typing import Self

from eaip.app.lifecycle import ApplicationLifecycle
from eaip.capabilities.registry import CapabilityRegistry
from eaip.core.feature_flags import FeatureFlagRegistry
from eaip.dependency_injection.container import Container
from eaip.dependency_injection.scope import Scope
from eaip.events.bus import EventBus
from eaip.health.checks import HealthCheck
from eaip.health.reporter import HealthReporter
from eaip.infrastructure.clock import SystemClock
from eaip.infrastructure.id_generator import UuidIdGenerator
from eaip.infrastructure.secret_provider import EnvSecretProvider
from eaip.lifecycle.manager import LifecycleManager
from eaip.logging.config import configure_logging
from eaip.logging.context import get_logger
from eaip.metrics.metrics import Meter
from eaip.platform.platform import Platform
from eaip.plugins.loader import PluginLoader
from eaip.plugins.plugin import Plugin
from eaip.plugins.registry import PluginRegistry
from eaip.ports.clock import ClockPort
from eaip.ports.id_generator import IdGeneratorPort
from eaip.ports.secret_provider import SecretProviderPort
from eaip.infrastructure.infrastructure import PlatformInfrastructure
from eaip.runtime.kernel import RuntimeKernel
from eaip.services.collection import ServiceCollection
from eaip.services.extensions import add_default_services
from eaip.settings.core_settings import PlatformSettings, load_platform_settings


class ApplicationBuilder:
    """Fluent builder that constructs a fully-wired application.

    Combines the Platform composition root, the Services layer, and
    the Runtime kernel into a single :class:`ApplicationLifecycle`.

    Usage::

        app = (
            ApplicationBuilder()
            .with_services(lambda s: s.add_singleton(IMyService, MyService))
            .with_settings(load_platform_settings())
            .build()
        )
        async with app:
            ...
    """

    def __init__(self) -> None:
        """Initialise a new builder with default service registrations."""
        self._services = ServiceCollection()
        add_default_services(self._services)
        self._settings: PlatformSettings | None = None
        self._plugins: list[Plugin] = []
        self._configure_logging: bool = True
        self._enable_runtime_kernel: bool = True
        self._log = get_logger("eaip.app.builder")

    # ------------------------------------------------------------------
    # Configuration knobs
    # ------------------------------------------------------------------

    def with_services(self, configure: Callable[[ServiceCollection], None]) -> Self:
        """Register services via a configuration callback.

        Args:
            configure: A callable that receives the ServiceCollection.

        Returns:
            Self for chaining.
        """
        configure(self._services)
        return self

    def with_settings(self, settings: PlatformSettings) -> Self:
        """Set the platform settings.

        Args:
            settings: The platform settings.

        Returns:
            Self for chaining.
        """
        self._settings = settings
        return self

    def with_plugin(self, plugin: Plugin) -> Self:
        """Add a plugin.

        Args:
            plugin: The plugin to install.

        Returns:
            Self for chaining.
        """
        self._plugins.append(plugin)
        return self

    def without_logging_configuration(self) -> Self:
        """Skip automatic logging configuration.

        Returns:
            Self for chaining.
        """
        self._configure_logging = False
        return self

    def without_runtime_kernel(self) -> Self:
        """Disable the RuntimeKernel (scheduler, hooks, modules).

        Returns:
            Self for chaining.
        """
        self._enable_runtime_kernel = False
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> ApplicationLifecycle:
        """Construct and return a fully-wired ApplicationLifecycle.

        Returns:
            A configured :class:`ApplicationLifecycle`.
        """
        settings = self._settings or load_platform_settings()

        if self._configure_logging:
            configure_logging(settings.logging.to_logging_config())

        # Build the DI container from service descriptors.
        container = self._services.build_container()
        self._wire_default_ports(container)
        container.register_instance(PlatformSettings, settings)

        # Create platform subsystems.
        feature_flags = self._build_feature_flags(settings)
        events = EventBus()
        health = HealthReporter(name=settings.core.app_name)
        lifecycle = LifecycleManager()
        capabilities = CapabilityRegistry()
        plugin_registry = PluginRegistry()
        plugin_loader = PluginLoader(plugin_registry)

        # Register subsystems in the container.
        container.register_instance(EventBus, events)
        container.register_instance(HealthReporter, health)
        container.register_instance(LifecycleManager, lifecycle)
        container.register_instance(CapabilityRegistry, capabilities)
        container.register_instance(PluginRegistry, plugin_registry)
        container.register_instance(PluginLoader, plugin_loader)
        container.register_instance(FeatureFlagRegistry, feature_flags)

        # Create the Platform.
        platform = Platform(
            settings=settings,
            container=container,
            lifecycle=lifecycle,
            events=events,
            health=health,
            capabilities=capabilities,
            plugins=plugin_registry,
            plugin_loader=plugin_loader,
            feature_flags=feature_flags,
        )

        # Install plugins.
        for plugin in self._plugins:
            plugin_loader.install(plugin)

        # Register Meter in container for DI access.
        if not container.has(Meter):
            meter = Meter(namespace="eaip")
            container.register_instance(Meter, meter)

        # Wire health checks from DI into the HealthReporter.
        self._wire_health_checks(container, health)

        # Build the runtime kernel if enabled.
        kernel: RuntimeKernel | None = None
        if self._enable_runtime_kernel:
            kernel = RuntimeKernel(platform)
            self._log.debug("app.runtime_kernel_created")

        # Build infrastructure (DB, cache, background tasks)
        infrastructure = PlatformInfrastructure(container, events, settings)

        self._log.info(
            "app.built",
            services=container.keys(),
            plugins=len(self._plugins),
            runtime_kernel=self._enable_runtime_kernel,
        )

        return ApplicationLifecycle(platform=platform, kernel=kernel, infrastructure=infrastructure)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _wire_default_ports(container: Container) -> None:
        if not container.has(ClockPort):
            container.register_factory(
                ClockPort,  # type: ignore[type-abstract]
                lambda _c: SystemClock(),
                scope=Scope.SINGLETON,
            )
        if not container.has(IdGeneratorPort):
            container.register_factory(
                IdGeneratorPort,  # type: ignore[type-abstract]
                lambda _c: UuidIdGenerator(),
                scope=Scope.SINGLETON,
            )
        if not container.has(SecretProviderPort):
            container.register_factory(
                SecretProviderPort,  # type: ignore[type-abstract]
                lambda _c: EnvSecretProvider(),
                scope=Scope.SINGLETON,
            )

    @staticmethod
    def _build_feature_flags(settings: PlatformSettings) -> FeatureFlagRegistry:
        registry = FeatureFlagRegistry()
        registry.apply_overrides(
            enabled=settings.feature_flags.enabled,
            disabled=settings.feature_flags.disabled,
        )
        return registry

    @staticmethod
    def _wire_health_checks(container: Container, health: HealthReporter) -> None:
        try:
            # Try to resolve individual HealthCheck instances from the container.
            for key in container.keys():  # noqa: SIM118
                if key is HealthCheck:
                    instance = container.try_resolve(key)
                    if instance is not None:
                        health.register(instance)
        except BaseException as exc:
            get_logger("eaip.app.builder").warning(
                "app.health_wire_failed",
                error=repr(exc),
            )
