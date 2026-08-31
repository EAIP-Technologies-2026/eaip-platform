"""Tests for DocPublisher."""

from __future__ import annotations

import pytest

from eaip.apidocs.exceptions import DocNotFoundError
from eaip.apidocs.models import DocFormat
from eaip.apidocs.publisher import DocPublisher


class TestDocPublisher:
    @pytest.fixture
    def publisher(self) -> DocPublisher:
        return DocPublisher()

    @pytest.mark.asyncio
    async def test_publish(self, publisher: DocPublisher) -> None:
        doc = await publisher.publish("1.0.0", DocFormat.MARKDOWN, "# API Docs")
        assert doc.source_version == "1.0.0"
        assert doc.format is DocFormat.MARKDOWN
        assert doc.content == "# API Docs"

    @pytest.mark.asyncio
    async def test_get_published(self, publisher: DocPublisher) -> None:
        await publisher.publish("1.0.0", DocFormat.OPENAPI_JSON, "{}")
        doc = await publisher.get_published("1.0.0", DocFormat.OPENAPI_JSON)
        assert doc is not None
        assert doc.content == "{}"

    @pytest.mark.asyncio
    async def test_get_published_not_found(self, publisher: DocPublisher) -> None:
        doc = await publisher.get_published("9.9.9", DocFormat.HTML)
        assert doc is None

    @pytest.mark.asyncio
    async def test_list_published(self, publisher: DocPublisher) -> None:
        await publisher.publish("1.0.0", DocFormat.MARKDOWN, "# Docs")
        await publisher.publish("1.0.0", DocFormat.OPENAPI_JSON, "{}")
        docs = await publisher.list_published()
        assert len(docs) == 2

    @pytest.mark.asyncio
    async def test_list_published_empty(self, publisher: DocPublisher) -> None:
        docs = await publisher.list_published()
        assert docs == []

    @pytest.mark.asyncio
    async def test_remove(self, publisher: DocPublisher) -> None:
        doc = await publisher.publish("1.0.0", DocFormat.MARKDOWN, "content")
        await publisher.remove(doc.id)
        assert await publisher.list_published() == []

    @pytest.mark.asyncio
    async def test_remove_not_found(self, publisher: DocPublisher) -> None:
        with pytest.raises(DocNotFoundError):
            await publisher.remove("nonexistent")

    @pytest.mark.asyncio
    async def test_count(self, publisher: DocPublisher) -> None:
        assert await publisher.count() == 0
        await publisher.publish("1.0.0", DocFormat.HTML, "<html/>")
        assert await publisher.count() == 1

    @pytest.mark.asyncio
    async def test_multiple_versions(self, publisher: DocPublisher) -> None:
        await publisher.publish("1.0.0", DocFormat.MARKDOWN, "v1")
        await publisher.publish("2.0.0", DocFormat.MARKDOWN, "v2")
        doc_v1 = await publisher.get_published("1.0.0", DocFormat.MARKDOWN)
        doc_v2 = await publisher.get_published("2.0.0", DocFormat.MARKDOWN)
        assert doc_v1 is not None and doc_v1.content == "v1"
        assert doc_v2 is not None and doc_v2.content == "v2"
