from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from eaip._version import __version__
from eaip.health.checks import DependencyClass
from eaip.logging.context import get_logger
from eaip.settings.core_settings import PlatformSettings, load_platform_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


__all__ = [
    "add_sentry_middleware",
    "init_sentry",
]

logger = logging.getLogger(__name__)

_sentry_sdk = None
_hub = None


def _get_sentry_sdk():
    global _sentry_sdk
    if _sentry_sdk is None:
        import sentry_sdk

        _sentry_sdk = sentry_sdk
    return _sentry_sdk


def _get_hub():
    global _hub
    if _hub is None:
        sentry = _get_sentry_sdk()
        _hub = sentry.Hub.current
    return _hub


def _resolve_release(settings: PlatformSettings) -> str:
    if settings.sentry.release:
        return settings.sentry.release
    return __version__


def _resolve_environment(settings: PlatformSettings) -> str:
    if settings.sentry.environment:
        return settings.sentry.environment
    return settings.core.environment_name


def init_sentry(settings: PlatformSettings | None = None) -> bool:
    """Initialise the Sentry SDK with production-safe defaults.

    Reads configuration from ``PlatformSettings`` (or the passed instance),
    then calls ``sentry_sdk.init()`` with the merged configuration.

    Args:
        settings: Optional ``PlatformSettings`` instance. If not provided,
            loads one from the environment via :func:`load_platform_settings`.

    Returns:
        True if Sentry was initialised, False if no DSN was configured.
    """
    if settings is None:
        settings = load_platform_settings()

    dsn = settings.sentry.dsn
    if not dsn:
        logger.info("sentry.skipped_no_dsn")
        return False

    sentry = _get_sentry_sdk()

    sentry.init(
        dsn=dsn,
        environment=_resolve_environment(settings),
        release=_resolve_release(settings),
        traces_sample_rate=settings.sentry.traces_sample_rate,
        send_default_pii=settings.sentry.send_default_pii,
        attach_stacktrace=settings.sentry.attach_stacktrace,
        _experiments={"record_sql_params": True},
    )

    log = get_logger("eaip.integrations.sentry")
    log.info("sentry.initialized", environment=_resolve_environment(settings))
    return True


class SentryFastAPIMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that captures unhandled exceptions via Sentry."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._log = get_logger("eaip.integrations.sentry.middleware")

    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            try:
                hub = _get_hub()
                hub.capture_exception(exc)
            except Exception:
                pass
            self._log.error("sentry.captured_exception", error=repr(exc))
            raise


def add_sentry_middleware(app: FastAPI) -> None:
    """Add the Sentry error-capture middleware to a FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_middleware(SentryFastAPIMiddleware)


class SentryHealthCheck:
    """Health check for the Sentry integration.

    Sentry is an optional dependency: it may report ``DEGRADED`` without
    affecting platform readiness.
    """

    name: str = "sentry"
    criticality = DependencyClass.OPTIONAL
    configured: bool = False

    def __init__(self) -> None:
        """Initialize SentryHealthCheck."""
        self._healthy: bool = False
        self._message: str = "Sentry has not been initialised"

    def mark_healthy(self) -> None:
        """Mark the Sentry integration as healthy."""
        self._healthy = True
        self.configured = True
        self._message = "Sentry integration is healthy"

    async def check(self):
        from eaip.health.checks import HealthReport, HealthStatus

        if self._healthy:
            return HealthReport(
                component=self.name,
                status=HealthStatus.HEALTHY,
                message=self._message,
            )
        return HealthReport(
            component=self.name,
            status=HealthStatus.DEGRADED,
            message=self._message,
        )
