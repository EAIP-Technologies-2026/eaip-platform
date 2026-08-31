"""DocPublisher — publishes and retrieves generated documentation."""

from __future__ import annotations

from typing import Any

from eaip.apidocs.events import DocPublished
from eaip.apidocs.exceptions import DocNotFoundError
from eaip.apidocs.models import DocFormat, GeneratedDoc


class DocPublisher:
    def __init__(self, event_bus: Any = None) -> None:
        self._published: dict[str, GeneratedDoc] = {}
        self._event_bus = event_bus

    async def publish(self, version: str, format: DocFormat, content: str) -> GeneratedDoc:
        doc_id = f"doc_{version}_{format.value}"
        doc = GeneratedDoc(
            id=doc_id,
            source_version=version,
            format=format,
            content=content,
        )
        self._published[doc_id] = doc
        if self._event_bus:
            self._event_bus.publish(
                DocPublished(
                    doc_id=doc_id,
                    source_version=version,
                    format=format.value,
                )
            )
        return doc

    async def get_published(self, version: str, format: DocFormat) -> GeneratedDoc | None:
        doc_id = f"doc_{version}_{format.value}"
        return self._published.get(doc_id)

    async def list_published(self) -> list[GeneratedDoc]:
        return list(self._published.values())

    async def remove(self, doc_id: str) -> None:
        if doc_id not in self._published:
            raise DocNotFoundError(doc_id)
        del self._published[doc_id]

    async def count(self) -> int:
        return len(self._published)


__all__ = ["DocPublisher"]
