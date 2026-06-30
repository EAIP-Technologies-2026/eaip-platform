"""The :class:`PlatformBuilder` — fluent construction of a :class:`Platform`."""

from __future__ import annotations

from typing import Self

from eaip.capabilities.registry import CapabilityRegistry
from eaip.core.feature_flags import FeatureFlagRegistry
from eaip.dependency_injection.container import Container
from eaip.dependency_injection.scope import Scope
from eaip.events.bus import EventBus
from eaip.health.reporter import HealthReporter
from eaip.infrastructure.clock import SystemClock
from eaip.infrastructure.id_generator import UuidIdGenerator
from eaip.infrastructure.secret_provider import EnvSecretProvider
from eaip.lifecycle.manager import LifecycleManager
from eaip.logging.config import configure_logging
from eaip.platform.platform import Platform
from eaip.plugins.loader import PluginLoader
from eaip.plugins.plugin import Plugin
from eaip.plugins.registry import PluginRegistry
from eaip.ports.clock import ClockPort
from eaip.ports.id_generator import IdGeneratorPort
from eaip.ports.secret_provider import SecretProviderPort
from eaip.settings.core_settings import PlatformSettings, load_platform_settings


class PlatformBuilder:
    """Fluent builder that composes every Foundation layer into a :class:`Platform`.

    Usage::

        platform = (
            PlatformBuilder()
            .with_settings(load_platform_settings())
            .with_plugin(my_plugin)
            .build()
        )
        async with platform:
            ...
    """

    def __init__(self) -> None:
        self._settings: PlatformSettings | None = None
        self._container: Container | None = None
        self._plugins: list[Plugin] = []
        self._configure_logging: bool = True

    # ------------------------------------------------------------------
    # Configuration knobs
    # ------------------------------------------------------------------
    def with_settings(self, settings: PlatformSettings) -> Self:
        self._settings = settings
        return self

    def with_container(self, container: Container) -> Self:
        """Inject a pre-built container; otherwise a fresh one is constructed."""
        self._container = container
        return self

    def with_plugin(self, plugin: Plugin) -> Self:
        self._plugins.append(plugin)
        return self

    def without_logging_configuration(self) -> Self:
        """Skip ``configure_logging()`` — caller manages logging itself."""
        self._configure_logging = False
        return self

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(self) -> Platform:
        settings = self._settings or load_platform_settings()

        if self._configure_logging:
            configure_logging(settings.logging.to_logging_config())

        container = self._container or Container()
        self._wire_default_ports(container)

        feature_flags = FeatureFlagRegistry()
        feature_flags.apply_overrides(
            enabled=settings.feature_flags.enabled,
            disabled=settings.feature_flags.disabled,
        )

        events = EventBus()
        health = HealthReporter(name=settings.core.app_name)
        lifecycle = LifecycleManager()
        capabilities = CapabilityRegistry()
        plugin_registry = PluginRegistry()
        plugin_loader = PluginLoader(plugin_registry)

        # Make the high-level subsystems resolvable from the container.
        container.register_instance(EventBus, events)
        container.register_instance(HealthReporter, health)
        container.register_instance(LifecycleManager, lifecycle)
        container.register_instance(CapabilityRegistry, capabilities)
        container.register_instance(PluginRegistry, plugin_registry)
        container.register_instance(PluginLoader, plugin_loader)
        container.register_instance(FeatureFlagRegistry, feature_flags)
        container.register_instance(PlatformSettings, settings)

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

        # Pre-install (but do not yet activate) declared plugins.
        for plugin in self._plugins:
            plugin_loader.install(plugin)

        return platform

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


__all__ = ["PlatformBuilder"]
