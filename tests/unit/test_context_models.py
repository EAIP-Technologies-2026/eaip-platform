"""Tests for context models."""

from __future__ import annotations

from eaip.context.models import (
    AssembledContext,
    CompressionConfig,
    CompressionStrategy,
    ContextBuilderConfig,
    ContextCacheConfig,
    ContextDocument,
    PromptRegistryEntry,
    PromptTemplate,
    PromptVersion,
)


class TestPromptTemplate:
    def test_defaults(self) -> None:
        tpl = PromptTemplate(
            template_id="t1",
            name="test",
            content="Hello {name}",
        )
        assert tpl.template_id == "t1"
        assert tpl.variables == ()
        assert tpl.version == "1.0.0"
        assert tpl.description == ""

    def test_with_variables(self) -> None:
        tpl = PromptTemplate(
            template_id="t2",
            name="greeting",
            content="Hello {name}, you are {age} years old",
            variables=("name", "age"),
        )
        assert tpl.variables == ("name", "age")


class TestPromptVersion:
    def test_defaults(self) -> None:
        pv = PromptVersion(version="2.0.0", content="New content")
        assert pv.version == "2.0.0"
        assert pv.change_log == ""
        assert pv.author == ""

    def test_with_metadata(self) -> None:
        pv = PromptVersion(
            version="1.1.0",
            content="Updated",
            change_log="Fixed typo",
            author="alice",
            metadata={"reviewed": True},
        )
        assert pv.change_log == "Fixed typo"
        assert pv.author == "alice"
        assert pv.metadata["reviewed"] is True


class TestPromptRegistryEntry:
    def test_defaults(self) -> None:
        entry = PromptRegistryEntry(prompt_id="p1")
        assert entry.prompt_id == "p1"
        assert entry.current_version == "1.0.0"
        assert entry.versions == ()

    def test_with_versions(self) -> None:
        v1 = PromptVersion(version="1.0.0", content="v1")
        entry = PromptRegistryEntry(
            prompt_id="p1",
            current_version="1.0.0",
            versions=(v1,),
        )
        assert len(entry.versions) == 1
        assert entry.current_version == "1.0.0"


class TestContextBuilderConfig:
    def test_defaults(self) -> None:
        cfg = ContextBuilderConfig()
        assert cfg.max_tokens == 4096
        assert cfg.relevance_threshold == 0.0
        assert cfg.include_sources is True
        assert cfg.deduplicate is True
        assert cfg.max_documents == 50

    def test_custom(self) -> None:
        cfg = ContextBuilderConfig(
            max_tokens=2048,
            relevance_threshold=0.7,
            include_sources=False,
            max_documents=10,
        )
        assert cfg.max_tokens == 2048
        assert cfg.relevance_threshold == 0.7
        assert cfg.include_sources is False
        assert cfg.max_documents == 10


class TestContextDocument:
    def test_defaults(self) -> None:
        doc = ContextDocument(content="some content")
        assert doc.content == "some content"
        assert doc.source == ""
        assert doc.relevance_score == 0.0
        assert doc.metadata == {}

    def test_with_source_and_score(self) -> None:
        doc = ContextDocument(
            content="important",
            source="memory:abc",
            relevance_score=0.95,
            metadata={"key": "val"},
        )
        assert doc.source == "memory:abc"
        assert doc.relevance_score == 0.95
        assert doc.metadata["key"] == "val"


class TestAssembledContext:
    def test_defaults(self) -> None:
        ctx = AssembledContext()
        assert ctx.documents == ()
        assert ctx.total_tokens == 0
        assert ctx.document_count == 0

    def test_with_documents(self) -> None:
        docs = (
            ContextDocument(content="a", relevance_score=0.9),
            ContextDocument(content="b", relevance_score=0.5),
        )
        ctx = AssembledContext(documents=docs, total_tokens=10, document_count=2)
        assert len(ctx.documents) == 2
        assert ctx.total_tokens == 10
        assert ctx.document_count == 2


class TestContextCacheConfig:
    def test_defaults(self) -> None:
        cfg = ContextCacheConfig()
        assert cfg.ttl_seconds == 300
        assert cfg.max_entries == 100

    def test_custom(self) -> None:
        cfg = ContextCacheConfig(ttl_seconds=600, max_entries=50)
        assert cfg.ttl_seconds == 600
        assert cfg.max_entries == 50


class TestCompressionConfig:
    def test_defaults(self) -> None:
        cfg = CompressionConfig()
        assert cfg.strategy is CompressionStrategy.EXTRACTIVE
        assert cfg.ratio == 0.5
        assert cfg.max_tokens == 2048

    def test_custom(self) -> None:
        cfg = CompressionConfig(
            strategy=CompressionStrategy.TRUNCATE,
            ratio=0.3,
            max_tokens=1024,
        )
        assert cfg.strategy is CompressionStrategy.TRUNCATE
        assert cfg.ratio == 0.3
        assert cfg.max_tokens == 1024


class TestFrozenModels:
    def test_models_are_frozen(self) -> None:
        cfg = ContextBuilderConfig()
        try:
            cfg.max_tokens = 999
            assert False, "Expected FrozenInstanceError"
        except Exception:
            pass

    def test_extra_forbidden(self) -> None:
        try:
            ContextDocument(content="x", unknown_field="y")  # type: ignore[call-arg]
            assert False, "Expected ValidationError"
        except Exception:
            pass
