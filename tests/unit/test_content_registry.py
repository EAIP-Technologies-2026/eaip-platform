"""Tests for ContentRegistry."""

from __future__ import annotations

import pytest

from eaip.content.exceptions import ContentNotFoundError
from eaip.content.models import ContentStatus, ContentType
from eaip.content.registry import ContentRegistry


class TestContentRegistry:
    def setup_method(self) -> None:
        self.registry = ContentRegistry()

    def test_create_and_get(self) -> None:
        item = self.registry.create(
            item_id="doc_1",
            name="Doc 1",
            type=ContentType.DOCUMENT,
            content_type="text/plain",
            body="hello",
            author="alice",
        )
        assert item.id == "doc_1"
        assert item.name == "Doc 1"
        assert item.status is ContentStatus.DRAFT
        assert item.author == "alice"
        assert item.content_hash != ""

        got = self.registry.get("doc_1")
        assert got.id == item.id
        assert got.body == item.body

    def test_get_not_found(self) -> None:
        with pytest.raises(ContentNotFoundError) as exc:
            self.registry.get("missing")
        assert "missing" in str(exc.value)

    def test_update(self) -> None:
        self.registry.create(
            item_id="doc_1",
            name="Doc 1",
            type=ContentType.DOCUMENT,
            content_type="text",
            body="hello",
        )
        updated = self.registry.update(
            "doc_1",
            name="Doc 1 Updated",
            body="updated body",
            author="bob",
        )
        assert updated.name == "Doc 1 Updated"
        assert updated.body == "updated body"
        assert updated.author == "bob"
        assert updated.content_hash != ""

    def test_update_not_found(self) -> None:
        with pytest.raises(ContentNotFoundError):
            self.registry.update("missing", name="N")

    def test_delete(self) -> None:
        self.registry.create(
            item_id="doc_1",
            name="Doc 1",
            type=ContentType.DOCUMENT,
            content_type="text",
            body="hello",
        )
        self.registry.delete("doc_1")
        with pytest.raises(ContentNotFoundError):
            self.registry.get("doc_1")

    def test_delete_not_found(self) -> None:
        with pytest.raises(ContentNotFoundError):
            self.registry.delete("missing")

    def test_list(self) -> None:
        self.registry.create("a", "A", ContentType.DOCUMENT, "text", "a")
        self.registry.create("b", "B", ContentType.CONFIG, "json", "{}")
        items = self.registry.list_items()
        assert len(items) == 2

    def test_search_by_tags(self) -> None:
        self.registry.create(
            "doc_1",
            "Doc 1",
            ContentType.DOCUMENT,
            "text",
            "body",
            tags=("alpha", "beta"),
        )
        self.registry.create(
            "doc_2",
            "Doc 2",
            ContentType.DOCUMENT,
            "text",
            "body",
            tags=("alpha",),
        )
        results = self.registry.search_by_tags("alpha")
        assert len(results) == 2
        results = self.registry.search_by_tags("alpha", "beta")
        assert len(results) == 1

    def test_search_by_type(self) -> None:
        self.registry.create("a", "A", ContentType.DOCUMENT, "text", "a")
        self.registry.create("b", "B", ContentType.CONFIG, "json", "{}")
        docs = self.registry.search_by_type(ContentType.DOCUMENT)
        assert len(docs) == 1
        configs = self.registry.search_by_type(ContentType.CONFIG)
        assert len(configs) == 1

    def test_publish_item(self) -> None:
        self.registry.create(
            "doc_1",
            "Doc 1",
            ContentType.DOCUMENT,
            "text",
            "body",
            author="alice",
        )
        published = self.registry.publish_item("doc_1", author="alice")
        assert published.status is ContentStatus.PUBLISHED
        assert published.published_at is not None
        assert published.author == "alice"

    def test_publish_item_twice(self) -> None:
        self.registry.create("doc_1", "Doc 1", ContentType.DOCUMENT, "text", "body")
        self.registry.publish_item("doc_1")
        published_again = self.registry.publish_item("doc_1")
        assert published_again.status is ContentStatus.PUBLISHED

    def test_archive_item(self) -> None:
        self.registry.create("doc_1", "Doc 1", ContentType.DOCUMENT, "text", "body")
        archived = self.registry.archive_item("doc_1", author="alice")
        assert archived.status is ContentStatus.ARCHIVED
        assert archived.author == "alice"

    def test_deprecate_item(self) -> None:
        self.registry.create("doc_1", "Doc 1", ContentType.DOCUMENT, "text", "body")
        deprecated = self.registry.deprecate_item("doc_1", author="alice")
        assert deprecated.status is ContentStatus.DEPRECATED
        assert deprecated.author == "alice"

    def test_lifecycle_transitions(self) -> None:
        self.registry.create("doc_1", "Doc 1", ContentType.DOCUMENT, "text", "body")
        self.registry.publish_item("doc_1")
        assert self.registry.get("doc_1").status is ContentStatus.PUBLISHED
        self.registry.archive_item("doc_1")
        assert self.registry.get("doc_1").status is ContentStatus.ARCHIVED
        self.registry.deprecate_item("doc_1")
        assert self.registry.get("doc_1").status is ContentStatus.DEPRECATED

    def test_get_version_history(self) -> None:
        self.registry.create("doc_1", "Doc 1", ContentType.DOCUMENT, "text", "body")
        history = self.registry.get_version_history("doc_1")
        assert len(history) == 1
        assert history[0].id == "doc_1"
