"""The :class:`Platform` — the single object every capability depends on.

The Platform is a **composition root**: it owns the DI container, the
lifecycle manager, the registries, and the configured settings. It does
**not** implement business behaviour itself — that is delivered by future
engineering packages registering capabilities & plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.registry import CapabilityRegistry
from eaip.core.feature_flags import FeatureFlagRegistry
from eaip.dependency_injection.container import Container
from eaip.events.bus import EventBus
from eaip.health.reporter import HealthReporter
from eaip.lifecycle.manager import LifecycleManager
from eaip.lifecycle.phases import LifecyclePhase
from eaip.logging.context import bind_context, get_logger
from eaip.plugins.loader import PluginLoader
from eaip.plugins.registry import PluginRegistry
from eaip.settings.core_settings import PlatformSettings

if TYPE_CHECKING:  # pragma: no cover
    pass


class Platform:
    """The composition root for every running EAIP instance.

    A ``Platform`` is constructed via :class:`PlatformBuilder` or the
    convenience function :func:`eaip.application.build_platform`. Direct
    instantiation is discouraged outside tests.
    """

    __slots__ = (
        "_capabilities",
        "_container",
        "_events",
        "_feature_flags",
        "_health",
        "_lifecycle",
        "_log",
        "_plugin_loader",
        "_plugins",
        "_settings",
    )

    def __init__(
        self,
        *,
        settings: PlatformSettings,
        container: Container,
        lifecycle: LifecycleManager,
        events: EventBus,
        health: HealthReporter,
        capabilities: CapabilityRegistry,
        plugins: PluginRegistry,
        plugin_loader: PluginLoader,
        feature_flags: FeatureFlagRegistry,
    ) -> None:
        self._settings = settings
        self._container = container
        self._lifecycle = lifecycle
        self._events = events
        self._health = health
        self._capabilities = capabilities
        self._plugins = plugins
        self._plugin_loader = plugin_loader
        self._feature_flags = feature_flags
        self._log = get_logger("eaip.platform")

    # ------------------------------------------------------------------
    # Identity & version
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return self._settings.core.app_name

    @property
    def version(self) -> str:
        from eaip._version import __version__

        return __version__

    @property
    def settings(self) -> PlatformSettings:
        return self._settings

    @property
    def phase(self) -> LifecyclePhase:
        return self._lifecycle.phase

    # ------------------------------------------------------------------
    # Composed subsystems (read-only access)
    # ------------------------------------------------------------------
    @property
    def container(self) -> Container:
        return self._container

    @property
    def lifecycle(self) -> LifecycleManager:
        return self._lifecycle

    @property
    def events(self) -> EventBus:
        return self._events

    @property
    def health(self) -> HealthReporter:
        return self._health

    @property
    def capabilities(self) -> CapabilityRegistry:
        return self._capabilities

    @property
    def plugins(self) -> PluginRegistry:
        return self._plugins

    @property
    def plugin_loader(self) -> PluginLoader:
        return self._plugin_loader

    @property
    def feature_flags(self) -> FeatureFlagRegistry:
        return self._feature_flags

    # ------------------------------------------------------------------
    # Lifecycle convenience
    # ------------------------------------------------------------------
    async def start(self) -> None:
        bind_context(
            app=self.name,
            env=str(self._settings.core.environment),
            instance=self._settings.core.instance_id,
            version=self.version,
        )
        self._log.info("platform.starting")
        await self._lifecycle.start()
        await self._plugin_loader.activate_all(self)
        self._log.info("platform.running")

    async def stop(self) -> None:
        self._log.info("platform.stopping")
        try:
            await self._plugin_loader.deactivate_all(self)
        finally:
            await self._lifecycle.stop()
        self._log.info("platform.stopped")

    async def __aenter__(self) -> Platform:
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()


__all__ = ["Platform"]
