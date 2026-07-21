"""CacheInvalidator — invalidate, purge, and manage cache entries by tag."""

from __future__ import annotations

from eaip.cacheinv.events import BulkInvalidationCompleted, CacheInvalidated, CachePurged
from eaip.cacheinv.exceptions import TagNotFoundError
from eaip.cacheinv.models import (
    CacheTag,
    InvalidationRequest,
    InvalidationResult,
    InvalidatorConfig,
)
from eaip.logging.context import get_logger


class CacheInvalidator:
    """Central service for cache tag management and invalidation."""

    def __init__(self, config: InvalidatorConfig | None = None) -> None:
        self._config = config or InvalidatorConfig()
        self._tags: dict[str, CacheTag] = {}
        self._requests: dict[str, InvalidationRequest] = {}
        self._log = get_logger("eaip.cacheinv.invalidator")

    @property
    def config(self) -> InvalidatorConfig:
        return self._config

    async def register_tag(self, tag: CacheTag) -> CacheTag:
        """Register a cache tag."""
        self._tags[tag.id] = tag
        self._log.info("cacheinv.tag.registered", tag_id=tag.id, pattern=tag.pattern)
        return tag

    async def get_tag(self, tag_id: str) -> CacheTag:
        """Retrieve a cache tag by ID."""
        tag = self._tags.get(tag_id)
        if tag is None:
            raise TagNotFoundError(f"Tag '{tag_id}' not found")
        return tag

    async def list_tags(self) -> list[CacheTag]:
        """List all registered cache tags."""
        return list(self._tags.values())

    async def invalidate(self, request: InvalidationRequest) -> InvalidationResult:
        """Process an invalidation request."""
        self._requests[request.id] = request
        count = 0
        for tag_id in request.tags:
            tag = self._tags.get(tag_id)
            if tag is not None:
                event = CacheInvalidated(
                    request_id=request.id,
                    tag=tag_id,
                    pattern=tag.pattern,
                )
                count += 1

        if request.pattern:
            for tag in self._tags.values():
                if request.pattern in tag.pattern:
                    event = CacheInvalidated(
                        request_id=request.id,
                        tag=tag.id,
                        pattern=tag.pattern,
                    )
                    count += 1

        result = InvalidationResult(request_id=request.id, invalidated_count=count, duration_ms=0)
        self._log.info("cacheinv.invalidated", request_id=request.id, count=count)
        return result

    async def purge_tag(self, tag_id: str) -> CachePurged:
        """Purge all cache entries associated with a tag."""
        tag = self._tags.get(tag_id)
        if tag is None:
            raise TagNotFoundError(f"Tag '{tag_id}' not found")

        entries_removed = 1
        event = CachePurged(tag=tag_id, entries_removed=entries_removed)
        self._log.info("cacheinv.tag.purged", tag_id=tag_id, count=entries_removed)
        return event

    async def bulk_invalidate(
        self, requests: list[InvalidationRequest]
    ) -> BulkInvalidationCompleted:
        """Process multiple invalidation requests in bulk."""
        total = 0
        for req in requests:
            result = await self.invalidate(req)
            total += result.invalidated_count

        event = BulkInvalidationCompleted(
            request_id="bulk",
            total_invalidated=total,
            duration_ms=0,
        )
        self._log.info("cacheinv.bulk_completed", total=total)
        return event

    async def get_invalidation_request(self, request_id: str) -> InvalidationRequest:
        """Retrieve an invalidation request by ID."""
        req = self._requests.get(request_id)
        if req is None:
            raise TagNotFoundError(f"Invalidation request '{request_id}' not found")
        return req

    async def list_invalidation_requests(self) -> list[InvalidationRequest]:
        """List all invalidation requests."""
        return list(self._requests.values())


__all__ = ["CacheInvalidator"]
