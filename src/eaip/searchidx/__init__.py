"""Search Indexing & Caching — index management, caching, cache warming.

Bundle-078 of the EAIP Platform Foundation Milestone.
"""

from __future__ import annotations

from eaip.searchidx.cache_warmer import CacheWarmer
from eaip.searchidx.events import (
    CacheHit,
    CacheInvalidated,
    CacheMiss,
    CacheWarmingCompleted,
    CacheWarmingStarted,
    IndexBuildCompleted,
    IndexBuildFailed,
    IndexBuildStarted,
    IndexCreated,
    IndexDeleted,
)
from eaip.searchidx.exceptions import (
    CacheError,
    CacheNotFoundError,
    IndexBuildError,
    IndexNotFoundError,
    SearchIndexError,
)
from eaip.searchidx.health import SearchIndexHealthCheck
from eaip.searchidx.index_manager import IndexManager
from eaip.searchidx.integration import SearchIndexRuntimeModule
from eaip.searchidx.models import (
    CachePolicy,
    IndexField,
    IndexJob,
    SearchCacheConfig,
    SearchIndex,
)
from eaip.searchidx.search_cache import SearchCache

__all__ = [
    "CacheError",
    "CacheHit",
    "CacheInvalidated",
    "CacheMiss",
    "CacheNotFoundError",
    "CachePolicy",
    "CacheWarmer",
    "CacheWarmingCompleted",
    "CacheWarmingStarted",
    "IndexBuildCompleted",
    "IndexBuildError",
    "IndexBuildFailed",
    "IndexBuildStarted",
    "IndexCreated",
    "IndexDeleted",
    "IndexField",
    "IndexJob",
    "IndexManager",
    "IndexNotFoundError",
    "SearchCache",
    "SearchCacheConfig",
    "SearchIndex",
    "SearchIndexError",
    "SearchIndexHealthCheck",
    "SearchIndexRuntimeModule",
]
