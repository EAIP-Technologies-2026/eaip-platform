"""API Extensions — advanced gateway capabilities.

Provides API composition (aggregating multiple endpoints into one response),
response caching with TTL and LRU eviction, rate-limit policy engine with
sliding-window counters, and response transformation (field mapping, header
modification, body filtering).
"""

from __future__ import annotations

from eaip.apiext.caching import ResponseCache
from eaip.apiext.composition import ApiComposer
from eaip.apiext.events import (
    CacheHit,
    CacheInvalidated,
    CacheMiss,
    CompositionExecuted,
    PolicyCreated,
    PolicyUpdated,
    RateLimitApplied,
    RateLimitExceeded,
    TransformApplied,
)
from eaip.apiext.exceptions import (
    ApiExtError,
    CacheError,
    CompositionError,
    PolicyNotFoundError,
    RateLimitExceededError,
    TransformError,
)
from eaip.apiext.health import ApiExtHealthCheck
from eaip.apiext.integration import ApiExtRuntimeModule
from eaip.apiext.models import (
    ApiComposition,
    ApiCompositionConfig,
    CachedResponse,
    MergeStrategy,
    RateLimitPolicy,
    ResponseTransform,
)
from eaip.apiext.rate_limit_policy import RateLimitPolicyEngine
from eaip.apiext.transforms import ResponseTransformer

__all__ = [
    "ApiComposer",
    "ApiComposition",
    "ApiCompositionConfig",
    "ApiExtError",
    "ApiExtHealthCheck",
    "ApiExtRuntimeModule",
    "CacheError",
    "CacheHit",
    "CacheInvalidated",
    "CacheMiss",
    "CachedResponse",
    "CompositionError",
    "CompositionExecuted",
    "MergeStrategy",
    "PolicyCreated",
    "PolicyNotFoundError",
    "PolicyUpdated",
    "RateLimitApplied",
    "RateLimitExceeded",
    "RateLimitExceededError",
    "RateLimitPolicy",
    "RateLimitPolicyEngine",
    "ResponseCache",
    "ResponseTransform",
    "ResponseTransformer",
    "TransformApplied",
    "TransformError",
]
