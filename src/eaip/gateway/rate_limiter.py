"""Token-bucket rate limiter with a sliding window."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Sequence
from threading import Lock

from eaip.gateway.models import RateLimitConfig


class _Bucket:
    """Sliding-window state for a single key."""

    __slots__ = ("timestamps",)

    def __init__(self) -> None:
        self.timestamps: list[float] = []


class RateLimiter:
    """In-memory rate limiter using a sliding-window algorithm.

    Each key (typically an API key ID or subject) gets its own window.
    Thread-safe via a per-instance lock.
    """

    def __init__(self) -> None:
        """Initialize the rate limiter with no active buckets."""
        self._buckets: dict[str, _Bucket] = defaultdict(_Bucket)
        self._lock = Lock()

    def check_limit(self, key: str, config: RateLimitConfig) -> bool:
        """Check whether *key* is allowed under *config*.

        If the key is within the limit the call counts toward the limit.
        Returns ``True`` when the request is allowed, ``False`` when it
        would exceed the limit.
        """
        now = time.monotonic()
        window_start = now - config.window_seconds

        with self._lock:
            bucket = self._buckets[key]
            # Prune expired timestamps.
            bucket.timestamps = _prune(bucket.timestamps, window_start)

            if len(bucket.timestamps) >= config.max_requests:
                return False

            bucket.timestamps.append(now)
            return True

    def reset(self, key: str | None = None) -> None:
        """Clear the bucket for *key*, or all buckets if *key* is ``None``."""
        with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)


def _prune(timestamps: Sequence[float], before: float) -> list[float]:
    """Return only timestamps >= *before* while preserving order."""
    return [ts for ts in timestamps if ts >= before]


__all__ = ["RateLimiter"]
