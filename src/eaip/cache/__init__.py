"""Distributed caching & data grid — in-memory cache, multi-level manager, health checks.

Bundle-079 of the EAIP Platform Foundation Milestone.
"""

from eaip.cache.events import (
    CacheCleared,
    CacheEntryEvicted,
    CacheEntryExpired,
    CacheHit,
    CacheMiss,
)
from eaip.cache.exceptions import CacheError, CacheMissError, CacheStorageError
from eaip.cache.health import CacheHealthCheck
from eaip.cache.integration import CacheRuntimeModule
from eaip.cache.manager import CacheManager
from eaip.cache.models import CacheConfig, CacheEntry, CacheStats
from eaip.cache.provider import CacheProvider, InMemoryCache, NullCache

__all__ = [
    "CacheCleared",
    "CacheConfig",
    "CacheEntry",
    "CacheEntryEvicted",
    "CacheEntryExpired",
    "CacheError",
    "CacheHealthCheck",
    "CacheHit",
    "CacheManager",
    "CacheMiss",
    "CacheMissError",
    "CacheProvider",
    "CacheRuntimeModule",
    "CacheStats",
    "CacheStorageError",
    "InMemoryCache",
    "NullCache",
]
