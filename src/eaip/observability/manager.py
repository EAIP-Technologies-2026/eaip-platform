from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.ports.observability import ObservabilityProvider
from eaip.settings.core_settings import PlatformSettings, load_platform_settings

if TYPE_CHECKING:
    pass

__all__ = [
    "ObservabilityManager",
    "build_observability_manager",
]

log = get_logger("eaip.observability")


class ObservabilityManager:
    """Manages a collection of observability providers.

    Providers are registered by name and started/stopped as a group.
    The composite follows the same pattern as other EAIP subsystems:
    lifecycle-aware, health-reported, and settings-driven.
    """

    def __init__(self, settings: PlatformSettings | None = None) -> None:
        """Initialise the manager.

        Args:
            settings: Optional PlatformSettings; loads from env if not provided.
        """
        self._settings = settings or load_platform_settings()
        self._providers: dict[str, ObservabilityProvider] = {}
        self._log = log

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, provider: ObservabilityProvider) -> None:
        """Register an observability provider.

        Args:
            provider: The provider instance.

        Raises:
            ValueError: If a provider with the same name is already registered.
        """
        if provider.name in self._providers:
            raise ValueError(
                f"observability provider {provider.name!r} already registered",
            )
        self._providers[provider.name] = provider
        self._log.info("observability.provider.registered", name=provider.name)

    def provider(self, name: str) -> ObservabilityProvider | None:
        """Return a registered provider by name, or None."""
        return self._providers.get(name)

    def providers(self) -> dict[str, ObservabilityProvider]:
        """Return a copy of all registered providers."""
        return dict(self._providers)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_all(self) -> None:
        """Start all registered providers."""
        for name, provider in self._providers.items():
            try:
                provider.start()
                self._log.info("observability.provider.started", name=name)
            except Exception as exc:
                self._log.error(
                    "observability.provider.start_failed",
                    name=name,
                    error=repr(exc),
                )

    def stop_all(self) -> None:
        """Stop all providers in reverse registration order."""
        for name in reversed(list(self._providers)):
            try:
                self._providers[name].stop()
                self._log.info("observability.provider.stopped", name=name)
            except Exception as exc:
                self._log.error(
                    "observability.provider.stop_failed",
                    name=name,
                    error=repr(exc),
                )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_report(self) -> dict[str, dict[str, str]]:
        """Return a health snapshot for all providers.

        Returns:
            Mapping of provider name to health info.
        """
        result: dict[str, dict[str, str]] = {}
        for name, provider in self._providers.items():
            healthy = provider.is_healthy()
            result[name] = {
                "status": "healthy" if healthy else "degraded",
                "registered": "true",
            }
        return result

    # ------------------------------------------------------------------
    # Database provider tagging
    # ------------------------------------------------------------------

    def tag_database_provider(self, provider_name: str) -> None:
        """Tag all registered providers with the active database provider.

        Args:
            provider_name: The active database provider name (e.g. ``"local"`` or ``"neon"``).
        """
        for name, provider in self._providers.items():
            try:
                provider.set_tag("db_provider", provider_name)
                self._log.debug(
                    "observability.db_tag_set", provider=name, provider_name=provider_name
                )
            except Exception as exc:
                self._log.warning(
                    "observability.db_tag_failed",
                    provider=name,
                    error=repr(exc),
                )


def build_observability_manager(settings: PlatformSettings | None = None) -> ObservabilityManager:
    """Construct an ObservabilityManager with all configured providers.

    Reads settings, creates providers, and registers them.
    Providers that lack required configuration (e.g. missing DSN/API key)
    are registered but remain unstarted until ``start_all()`` is called.

    Args:
        settings: Optional PlatformSettings; loads from env if not provided.

    Returns:
        A fully configured ObservabilityManager.
    """
    if settings is None:
        settings = load_platform_settings()

    manager = ObservabilityManager(settings)

    # --- Sentry ---
    sentry_provider = _build_sentry_provider(settings)
    if sentry_provider is not None:
        manager.register(sentry_provider)

    # --- Better Stack ---
    from eaip.integrations.betterstack import BetterStackProvider

    betterstack = BetterStackProvider(settings.better_stack)
    manager.register(betterstack)

    return manager


def _build_sentry_provider(settings: PlatformSettings) -> ObservabilityProvider | None:
    if not settings.sentry.dsn:
        return None
    init_sentry(settings)
    return _SentryAdapter()


def init_sentry(settings: PlatformSettings) -> bool:
    """Initialise the Sentry SDK (delegates to sentry integration module)."""
    from eaip.integrations.sentry import init_sentry as _do_init

    return _do_init(settings)


class _SentryAdapter(ObservabilityProvider):
    """Wraps the existing Sentry integration behind the ObservabilityProvider protocol."""

    name: str = "sentry"

    def __init__(self) -> None:
        self._log = log

    def start(self) -> None:
        self._log.info("observability.sentry.started")

    def stop(self) -> None:
        self._log.info("observability.sentry.stopped")

    def is_healthy(self) -> bool:
        from eaip.integrations.sentry import _get_hub

        hub = _get_hub()
        return hub is not None

    def capture_error(self, error: Exception, context: dict[str, any] | None = None) -> str | None:
        from eaip.integrations.sentry import _get_hub

        hub = _get_hub()
        if hub is None:
            return None
        event_id = hub.capture_exception(error)
        self._log.debug("sentry.captured_error", event_id=event_id, error=repr(error))
        return event_id

    def capture_message(
        self, message: str, level: str = "info", context: dict[str, any] | None = None
    ) -> str | None:
        from eaip.integrations.sentry import _get_hub

        hub = _get_hub()
        if hub is None:
            return None
        event_id = hub.capture_message(message, level=level)
        self._log.debug("sentry.captured_message", event_id=event_id, level=level)
        return event_id

    def capture_deployment(self, release: str, environment: str) -> str | None:
        self._log.info("sentry.captured_deployment", release=release, environment=environment)
        return None

    def set_tag(self, key: str, value: str) -> None:
        from eaip.integrations.sentry import _get_hub

        hub = _get_hub()
        if hub is not None:
            hub.set_tag(key, value)
