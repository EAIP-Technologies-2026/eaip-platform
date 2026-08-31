"""Tests for document ingestion pipeline."""

from __future__ import annotations

import pytest

from eaip.knowledge.embedding import MockEmbeddingProvider
from eaip.knowledge.exceptions import UnsupportedFormatError
from eaip.knowledge.ingestion import (
    HTMLParser,
    IngestionPipeline,
    MarkdownParser,
    TextParser,
    get_parser,
    register_parser,
)
from eaip.knowledge.models import (
    DocumentFormat,
    IndexingStatus,
    IngestionConfig,
)


class _MockVectorStore:
    def __init__(self) -> None:
        self.upserted: list[list] = []

    async def create_collection(self, name: str, dimensions: int, **kwargs: str) -> None:
        pass

    async def upsert_points(self, collection: str, chunks: list) -> None:
        self.upserted.append(chunks)

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        pass

    async def search(self, collection: str, query):  # type: ignore[no-untyped-def]
        return []

    async def delete_collection(self, name: str) -> None:
        pass

    async def list_collections(self) -> list[str]:
        return []

    async def collection_info(self, name: str) -> dict:
        return {}


class TestTextParser:
    @pytest.mark.asyncio
    async def test_parse_utf8(self) -> None:
        parser = TextParser()
        result = await parser.parse(b"Hello world")
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_parse_binary(self) -> None:
        parser = TextParser()
        result = await parser.parse(b"\xff\xfe\x00Hello")
        assert "Hello" in result


class TestMarkdownParser:
    @pytest.mark.asyncio
    async def test_parse_removes_markdown(self) -> None:
        parser = MarkdownParser()
        md = b"# Title\n\n**bold** text and [link](http://example.com)"
        result = await parser.parse(md)
        assert "Title" in result
        assert "bold" in result
        assert "link" in result
        assert "http://" not in result

    @pytest.mark.asyncio
    async def test_parse_table(self) -> None:
        parser = MarkdownParser()
        md = b"| A | B |\n| --- | --- |\n| 1 | 2 |"
        result = await parser.parse(md)
        assert "1" in result or "2" in result


class TestHTMLParser:
    @pytest.mark.asyncio
    async def test_parse_extracts_text(self) -> None:
        parser = HTMLParser()
        html = b"<html><body><p>Hello <b>world</b></p></body></html>"
        result = await parser.parse(html)
        assert "Hello" in result
        assert "world" in result

    @pytest.mark.asyncio
    async def test_parse_skips_script(self) -> None:
        parser = HTMLParser()
        html = b"<html><body><p>Text</p><script>var x=1;</script></body></html>"
        result = await parser.parse(html)
        assert "Text" in result
        assert "var x" not in result


class TestGetParser:
    def test_get_parser_txt(self) -> None:
        parser = get_parser(DocumentFormat.TXT)
        assert isinstance(parser, TextParser)

    def test_get_parser_markdown(self) -> None:
        parser = get_parser(DocumentFormat.MARKDOWN)
        assert isinstance(parser, MarkdownParser)

    def test_get_parser_html(self) -> None:
        parser = get_parser(DocumentFormat.HTML)
        assert isinstance(parser, HTMLParser)

    def test_unknown_format_raises(self) -> None:

        with pytest.raises(UnsupportedFormatError):
            get_parser("unknown")  # type: ignore[arg-type]


class TestRegisterParser:
    def test_register_custom(self) -> None:
        original = get_parser(DocumentFormat.TXT)
        custom = TextParser()
        register_parser(DocumentFormat.TXT, custom)
        assert get_parser(DocumentFormat.TXT) is custom
        register_parser(DocumentFormat.TXT, original)


class TestIngestionPipeline:
    @pytest.mark.asyncio
    async def test_ingest_txt(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        config = IngestionConfig(collection="test")
        pipeline = IngestionPipeline(
            config=config, vector_store=store, embedding_provider=embedding
        )

        result = await pipeline.ingest(
            "doc1", b"Hello world content", DocumentFormat.TXT, title="Test"
        )
        assert result.status is IndexingStatus.INDEXED
        assert result.chunk_count > 0
        assert result.document.document_id == "doc1"
        assert len(store.upserted) == 1

    @pytest.mark.asyncio
    async def test_ingest_markdown(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        config = IngestionConfig(collection="test")
        pipeline = IngestionPipeline(
            config=config, vector_store=store, embedding_provider=embedding
        )

        result = await pipeline.ingest(
            "doc2", b"# Title\n\nParagraph.", DocumentFormat.MARKDOWN, title="MD"
        )
        assert result.status is IndexingStatus.INDEXED

    @pytest.mark.asyncio
    async def test_ingest_failed_format(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        config = IngestionConfig(collection="test")
        pipeline = IngestionPipeline(
            config=config, vector_store=store, embedding_provider=embedding
        )

        result = await pipeline.ingest("doc3", b"fake", "unknown_format", title="Bad")  # type: ignore[arg-type]
        assert result.status is IndexingStatus.FAILED

    @pytest.mark.asyncio
    async def test_ingest_with_events(self) -> None:
        store = _MockVectorStore()
        embedding = MockEmbeddingProvider()
        config = IngestionConfig(collection="test")
        events: list = []

        def publisher(event: object) -> None:
            events.append(event)

        pipeline = IngestionPipeline(
            config=config,
            vector_store=store,
            embedding_provider=embedding,
            event_publisher=publisher,
        )
        result = await pipeline.ingest(
            "doc4", b"Event test content", DocumentFormat.TXT, title="Events"
        )
        assert result.status is IndexingStatus.INDEXED
        assert len(events) > 0
