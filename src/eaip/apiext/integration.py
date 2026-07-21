"""Runtime integration — ApiExtRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.apiext.caching import ResponseCache
from eaip.apiext.composition import ApiComposer
from eaip.apiext.health import ApiExtHealthCheck
from eaip.apiext.rate_limit_policy import RateLimitPolicyEngine
from eaip.apiext.transforms import ResponseTransformer
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ApiExtRuntimeModule:
    """RuntimeModule that bootstraps the API Extensions subsystem during kernel start.

    On start:
      - Creates the composer, cache, rate-limit engine, and transformer.
      - Registers the API Extensions health check.
    On stop:
      - Cleans up cache and in-flight state.
    """

    name: str = "apiext"

    def __init__(
        self,
        composer: ApiComposer | None = None,
        cache: ResponseCache | None = None,
        rate_limit_engine: RateLimitPolicyEngine | None = None,
        transformer: ResponseTransformer | None = None,
    ) -> None:
        """Initialize the ApiExtRuntimeModule.

        Args:
            composer: An optional pre-configured composer.
            cache: An optional pre-configured cache.
            rate_limit_engine: An optional pre-configured rate-limit engine.
            transformer: An optional pre-configured transformer.
        """
        self._composer = composer or ApiComposer()
        self._cache = cache or ResponseCache()
        self._rate_limit_engine = rate_limit_engine or RateLimitPolicyEngine()
        self._transformer = transformer or ResponseTransformer()
        self._log = get_logger("eaip.apiext.integration")
        self._startup_duration: float = 0.0

    @property
    def composer(self) -> ApiComposer:
        """Return the configured composer."""
        return self._composer

    @property
    def cache(self) -> ResponseCache:
        """Return the configured cache."""
        return self._cache

    @property
    def rate_limit_engine(self) -> RateLimitPolicyEngine:
        """Return the configured rate-limit engine."""
        return self._rate_limit_engine

    @property
    def transformer(self) -> ResponseTransformer:
        """Return the configured transformer."""
        return self._transformer

    @property
    def startup_duration(self) -> float:
        """Return the last startup duration in seconds."""
        return self._startup_duration

    async def start(self, kernel: RuntimeKernel) -> None:
        """Bootstrap the API Extensions subsystem.

        Args:
            kernel: The runtime kernel.
        """
        self._log.info("apiext.module.start")
        t0 = time.monotonic()

        check = ApiExtHealthCheck(
            composer=self._composer,
            cache=self._cache,
            rate_limit_engine=self._rate_limit_engine,
            transformer=self._transformer,
        )
        kernel.platform.health.register(check)

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "apiext.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the API Extensions subsystem.

        Args:
            _kernel: The runtime kernel.
        """
        self._log.info("apiext.module.stop")
        await self._cache.clear()
        self._log.info("apiext.module.stopped")


__all__ = ["ApiExtRuntimeModule"]
