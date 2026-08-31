"""ContentRegistry - managed content registry with CRUD, search, and lifecycle operations."""

from __future__ import annotations

import hashlib
from typing import Any

from eaip.content.exceptions import ContentNotFoundError
from eaip.content.models import ContentConfig, ContentItem, ContentStatus, ContentType
from eaip.shared.time import utc_now


class ContentRegistry:
    """In-memory content registry with search and lifecycle management."""

    def __init__(self, config: ContentConfig | None = None) -> None:
        self._config = config or ContentConfig()
        self._items: dict[str, ContentItem] = {}

    @property
    def config(self) -> ContentConfig:
        return self._config

    def _compute_hash(self, body: str) -> str:
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def create(
        self,
        item_id: str,
        name: str,
        type: ContentType,
        content_type: str,
        body: str,
        *,
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
        author: str = "",
    ) -> ContentItem:
        content_hash = self._compute_hash(body)
        now = utc_now()
        item = ContentItem(
            id=item_id,
            name=name,
            type=type,
            content_type=content_type,
            body=body,
            status=self._config.default_status,
            tags=tags,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            author=author,
            content_hash=content_hash,
        )
        self._items[item_id] = item
        return item

    def get(self, item_id: str) -> ContentItem:
        item = self._items.get(item_id)
        if item is None:
            raise ContentNotFoundError(item_id)
        return item

    def update(
        self,
        item_id: str,
        *,
        name: str | None = None,
        body: str | None = None,
        tags: tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
        author: str = "",
    ) -> ContentItem:
        existing = self.get(item_id)
        new_body = body if body is not None else existing.body
        content_hash = self._compute_hash(new_body)
        updated = ContentItem(
            id=existing.id,
            name=name if name is not None else existing.name,
            type=existing.type,
            content_type=existing.content_type,
            body=new_body,
            version=existing.version,
            status=existing.status,
            tags=tags if tags is not None else existing.tags,
            metadata=metadata if metadata is not None else existing.metadata,
            created_at=existing.created_at,
            updated_at=utc_now(),
            published_at=existing.published_at,
            author=author or existing.author,
            checksum=existing.checksum,
            content_hash=content_hash,
        )
        self._items[item_id] = updated
        return updated

    def delete(self, item_id: str) -> None:
        if item_id not in self._items:
            raise ContentNotFoundError(item_id)
        del self._items[item_id]

    def list_items(self) -> list[ContentItem]:
        return list(self._items.values())

    def search_by_tags(self, *tags: str) -> list[ContentItem]:
        tag_set = set(tags)
        return [item for item in self._items.values() if tag_set.issubset(set(item.tags))]

    def search_by_type(self, type: ContentType) -> list[ContentItem]:
        return [item for item in self._items.values() if item.type == type]

    def publish_item(self, item_id: str, author: str = "") -> ContentItem:
        existing = self.get(item_id)
        if existing.status == ContentStatus.PUBLISHED:
            return existing
        now = utc_now()
        published = ContentItem(
            id=existing.id,
            name=existing.name,
            type=existing.type,
            content_type=existing.content_type,
            body=existing.body,
            version=existing.version,
            status=ContentStatus.PUBLISHED,
            tags=existing.tags,
            metadata=existing.metadata,
            created_at=existing.created_at,
            updated_at=now,
            published_at=now,
            author=author or existing.author,
            checksum=existing.checksum,
            content_hash=existing.content_hash,
        )
        self._items[item_id] = published
        return published

    def archive_item(self, item_id: str, author: str = "") -> ContentItem:
        existing = self.get(item_id)
        now = utc_now()
        archived = ContentItem(
            id=existing.id,
            name=existing.name,
            type=existing.type,
            content_type=existing.content_type,
            body=existing.body,
            version=existing.version,
            status=ContentStatus.ARCHIVED,
            tags=existing.tags,
            metadata=existing.metadata,
            created_at=existing.created_at,
            updated_at=now,
            published_at=existing.published_at,
            author=author or existing.author,
            checksum=existing.checksum,
            content_hash=existing.content_hash,
        )
        self._items[item_id] = archived
        return archived

    def deprecate_item(self, item_id: str, author: str = "") -> ContentItem:
        existing = self.get(item_id)
        now = utc_now()
        deprecated = ContentItem(
            id=existing.id,
            name=existing.name,
            type=existing.type,
            content_type=existing.content_type,
            body=existing.body,
            version=existing.version,
            status=ContentStatus.DEPRECATED,
            tags=existing.tags,
            metadata=existing.metadata,
            created_at=existing.created_at,
            updated_at=now,
            published_at=existing.published_at,
            author=author or existing.author,
            checksum=existing.checksum,
            content_hash=existing.content_hash,
        )
        self._items[item_id] = deprecated
        return deprecated

    def get_version_history(self, item_id: str) -> list[ContentItem]:
        return [self.get(item_id)]


__all__ = [
    "ContentRegistry",
]
