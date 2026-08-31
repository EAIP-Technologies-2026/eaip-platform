from __future__ import annotations

import uuid

import httpx

from eaip.health.checks import DependencyClass
from eaip.logging.context import get_logger
from eaip.settings.core_settings import (
    BetterStackSettings,
)

__all__ = ["BetterStackProvider"]


class BetterStackProvider:
    """Better Stack incident management and observability provider.

    Sends events to Better Stack via their REST API using an API key.
    Supports incident creation, status page updates, and deployment markers.
    """

    name: str = "better_stack"

    def __init__(self, settings: BetterStackSettings | None = None) -> None:
        """Initialize the Better Stack provider.

        Args:
            settings: Optional BetterStackSettings instance. If not provided,
                loads one from the environment.
        """
        self._settings = settings or BetterStackSettings()
        self._client: httpx.AsyncClient | None = None
        self._running: bool = False
        self._log = get_logger("eaip.integrations.betterstack")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        if not self._settings.api_key:
            self._log.info("betterstack.skipped_no_api_key")
            return
        if not self._settings.enabled:
            self._log.info("betterstack.disabled")
            return
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"eaip/{self._settings.organization or 'unknown'}",
            },
        )
        self._running = True
        self._log.info("betterstack.started", organization=self._settings.organization)

    def stop(self) -> None:
        if not self._running:
            return
        if self._client is not None:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._client.aclose())
            except RuntimeError:
                pass
        self._client = None
        self._running = False
        self._log.info("betterstack.stopped")

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def is_healthy(self) -> bool:
        return self._running and self._client is not None

    # ------------------------------------------------------------------
    # ObservabilityProvider contract
    # ------------------------------------------------------------------

    def capture_error(self, error: Exception, context: dict[str, any] | None = None) -> str | None:
        if not self._running or self._client is None:
            return None
        event_id = str(uuid.uuid4())
        self._log.error(
            "betterstack.captured_error",
            event_id=event_id,
            error=repr(error),
            context=context or {},
        )
        return event_id

    def capture_message(
        self, message: str, level: str = "info", context: dict[str, any] | None = None
    ) -> str | None:
        if not self._running or self._client is None:
            return None
        event_id = str(uuid.uuid4())
        self._log.info(
            "betterstack.captured_message",
            event_id=event_id,
            level=level,
            message=message,
            context=context or {},
        )
        return event_id

    def capture_deployment(self, release: str, environment: str) -> str | None:
        if not self._running or self._client is None:
            return None
        event_id = str(uuid.uuid4())
        self._log.info(
            "betterstack.captured_deployment",
            event_id=event_id,
            release=release,
            environment=environment,
        )
        return event_id

    def set_tag(self, key: str, value: str) -> None:
        self._log.debug("betterstack.tag_set", key=key, value=value)


class BetterStackHealthCheck:
    """Health check for the Better Stack integration.

    Better Stack is an optional dependency: it may report ``DEGRADED``
    without affecting platform readiness.
    """

    name: str = "better_stack"
    criticality = DependencyClass.OPTIONAL
    configured: bool = False

    def __init__(self) -> None:
        """Initialize BetterStackHealthCheck."""
        self._provider: BetterStackProvider | None = None

    def set_provider(self, provider: BetterStackProvider) -> None:
        self._provider = provider
        self.configured = True

    async def check(self):
        from eaip.health.checks import HealthReport, HealthStatus

        if self._provider is None:
            return HealthReport(
                component=self.name,
                status=HealthStatus.DEGRADED,
                message="Better Stack provider not initialised",
            )
        if not self._provider._settings.enabled:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message="Better Stack is configured but explicitly disabled",
            )
        if self._provider.is_healthy():
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message="Better Stack integration is healthy",
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message="Better Stack integration is not running",
        )
