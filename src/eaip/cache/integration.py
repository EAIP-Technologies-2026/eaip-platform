"""Runtime integration — CacheRuntimeModule for kernel lifecycle."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from eaip.cache.health import CacheHealthCheck
from eaip.cache.manager import CacheManager
from eaip.cache.models import CacheConfig
from eaip.cache.provider import CacheProvider, InMemoryCache
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CacheRuntimeModule:
    """RuntimeModule that registers the caching subsystem with the kernel."""

    name: str = "cache"

    def __init__(
        self,
        config: CacheConfig | None = None,
        l2_provider: CacheProvider | None = None,
    ) -> None:
        """Initialize with optional config and L2 provider."""
        self._config = config or CacheConfig()
        self._l2_provider = l2_provider
        self._manager: CacheManager | None = None
        self._health_check: CacheHealthCheck | None = None
        self._startup_duration: float = 0.0
        self._log = get_logger("eaip.cache.integration")

    def create_manager(
        self,
        config: CacheConfig | None = None,
        l2_provider: CacheProvider | None = None,
    ) -> CacheManager:
        """Create a CacheManager with optional config/l2 override."""
        cfg = config or self._config
        l2 = l2_provider or self._l2_provider
        return CacheManager(config=cfg, l2_provider=l2)

    def create_in_memory_cache(
        self,
        max_entries: int = 10000,
        max_size_bytes: int = 0,
        namespace: str = "default",
    ) -> InMemoryCache:
        """Create an InMemoryCache instance."""
        return InMemoryCache(
            max_entries=max_entries,
            max_size_bytes=max_size_bytes,
            namespace=namespace,
        )

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the cache module and register with the kernel."""
        t0 = time.monotonic()
        self._log.info("cache.module.start")

        self._manager = CacheManager(config=self._config, l2_provider=self._l2_provider)
        self._health_check = CacheHealthCheck(manager=self._manager)

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="cache:framework",
                title="Distributed Cache & Data Grid",
                status=CapabilityStatus.ENABLED,
                tags=("cache", "data-grid", "distributed-cache"),
            )
        )

        self._startup_duration = time.monotonic() - t0
        self._log.info(
            "cache.module.complete",
            duration_s=round(self._startup_duration, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the cache module."""
        self._log.info("cache.module.stop")
        if self._manager is not None:
            await self._manager.close()
