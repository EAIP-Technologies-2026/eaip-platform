"""ContentVersioning - version management with rollback, diff, and history."""

from __future__ import annotations

import difflib
import hashlib
from typing import Any

from eaip.content.exceptions import ContentNotFoundError, VersionNotFoundError
from eaip.content.models import ContentConfig, ContentItem, ContentStatus, ContentType
from eaip.shared.time import utc_now


class ContentVersioning:
    """Version manager for content items with history and rollback."""

    def __init__(self, config: ContentConfig | None = None) -> None:
        self._config = config or ContentConfig()
        self._versions: dict[str, list[ContentItem]] = {}

    @property
    def config(self) -> ContentConfig:
        return self._config

    def _compute_hash(self, body: str) -> str:
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def create_version(
        self,
        item_id: str,
        body: str,
        change_log: str = "",
        *,
        name: str = "",
        type: ContentType = ContentType.DOCUMENT,
        content_type: str = "text/plain",
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
        author: str = "",
    ) -> ContentItem:
        versions = self._versions.setdefault(item_id, [])
        if len(versions) >= self._config.max_versions_per_item:
            versions.pop(0)
        version_num = len(versions) + 1
        version_str = f"0.{version_num}.0"
        now = utc_now()
        content_hash = self._compute_hash(body)
        item = ContentItem(
            id=item_id,
            name=name or f"item_{item_id}",
            type=type,
            content_type=content_type,
            body=body,
            version=version_str,
            status=ContentStatus.DRAFT,
            tags=tags,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            author=author,
            content_hash=content_hash,
        )
        versions.append(item)
        return item

    def get_version(self, item_id: str, version: str) -> ContentItem:
        versions = self._versions.get(item_id)
        if versions is None:
            raise ContentNotFoundError(item_id)
        for v in versions:
            if v.version == version:
                return v
        raise VersionNotFoundError(item_id, version)

    def list_versions(self, item_id: str) -> list[ContentItem]:
        versions = self._versions.get(item_id)
        if versions is None:
            raise ContentNotFoundError(item_id)
        return list(versions)

    def rollback(self, item_id: str, version: str) -> ContentItem:
        target = self.get_version(item_id, version)
        return self.create_version(
            item_id=item_id,
            body=target.body,
            change_log=f"rollback to version {version}",
            name=target.name,
            type=target.type,
            content_type=target.content_type,
            tags=target.tags,
            metadata=dict(target.metadata),
            author=target.author,
        )

    def diff_versions(self, item_id: str, v1: str, v2: str) -> list[str]:
        version1 = self.get_version(item_id, v1)
        version2 = self.get_version(item_id, v2)
        diff = difflib.unified_diff(
            version1.body.splitlines(keepends=True),
            version2.body.splitlines(keepends=True),
            fromfile=v1,
            tofile=v2,
        )
        return list(diff)

    def get_latest_version(self, item_id: str) -> ContentItem:
        versions = self._versions.get(item_id)
        if versions is None:
            raise ContentNotFoundError(item_id)
        return versions[-1]


__all__ = [
    "ContentVersioning",
]
