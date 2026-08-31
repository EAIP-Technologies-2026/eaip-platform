"""Runtime integration — GatewayRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.gateway.auth import ApiKeyStore
from eaip.gateway.health import GatewayHealthCheck
from eaip.gateway.middleware import (
    AuthMiddleware,
    CorsMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    RateLimitMiddleware,
)
from eaip.gateway.rate_limiter import RateLimiter
from eaip.gateway.router import ApiRouter
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class GatewayRuntimeModule:
    """RuntimeModule that bootstraps the API gateway during kernel start.

    On start:
      - Creates the router, pipeline, and default middlewares.
      - Registers the gateway health check.
    On stop:
      - Cleans up any in-flight state.
    """

    name: str = "gateway"

    def __init__(
        self,
        router: ApiRouter | None = None,
        key_store: ApiKeyStore | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Initialize the GatewayRuntimeModule.

        Args:
            router: An optional pre-configured router.
            key_store: An optional API key store.
            rate_limiter: An optional rate limiter.
        """
        self._key_store = key_store or ApiKeyStore()
        self._rate_limiter = rate_limiter or RateLimiter()
        self._router = router or ApiRouter()
        self._log = get_logger("eaip.gateway.integration")
        self._startup_duration: float = 0.0

    @property
    def router(self) -> ApiRouter:
        """Return the configured router."""
        return self._router

    @property
    def key_store(self) -> ApiKeyStore:
        """Return the configured key store."""
        return self._key_store

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    def _install_default_middlewares(self) -> None:
        pipeline = self._router.pipeline
        pipeline.add(LoggingMiddleware())
        pipeline.add(MetricsMiddleware())
        pipeline.add(AuthMiddleware(self._key_store))
        pipeline.add(RateLimitMiddleware(self._rate_limiter))
        pipeline.add(CorsMiddleware())

    async def start(self, kernel: RuntimeKernel) -> None:
        """Bootstrap the gateway subsystem.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("gateway.module.start")
        t0 = time.monotonic()

        self._install_default_middlewares()

        check = GatewayHealthCheck(self._router)
        kernel.platform.health.register(check)

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "gateway.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the gateway subsystem.

        Args:
            _kernel: The runtime kernel.
        """
        self._log.info("gateway.module.stop")
        self._log.info("gateway.module.stopped")


__all__ = ["GatewayRuntimeModule"]
