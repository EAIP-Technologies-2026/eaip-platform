"""Tests for ContentVersioning."""

from __future__ import annotations

import pytest

from eaip.content.exceptions import ContentNotFoundError, VersionNotFoundError
from eaip.content.models import ContentItem
from eaip.content.versioning import ContentVersioning


class TestContentVersioning:
    def setup_method(self) -> None:
        self.versioning = ContentVersioning()

    def test_create_version(self) -> None:
        item = self.versioning.create_version(
            item_id="doc_1",
            body="version 1 body",
            change_log="initial",
            author="alice",
        )
        assert item.id == "doc_1"
        assert item.version == "0.1.0"
        assert item.body == "version 1 body"
        assert item.author == "alice"
        assert isinstance(item, ContentItem)

    def test_list_versions(self) -> None:
        self.versioning.create_version("doc_1", "v1 body", "first")
        self.versioning.create_version("doc_1", "v2 body", "second")
        versions = self.versioning.list_versions("doc_1")
        assert len(versions) == 2
        assert versions[0].version == "0.1.0"
        assert versions[1].version == "0.2.0"

    def test_list_versions_not_found(self) -> None:
        with pytest.raises(ContentNotFoundError):
            self.versioning.list_versions("missing")

    def test_get_version(self) -> None:
        self.versioning.create_version("doc_1", "v1 body", "first")
        v = self.versioning.get_version("doc_1", "0.1.0")
        assert v.body == "v1 body"
        assert v.version == "0.1.0"

    def test_get_version_not_found(self) -> None:
        self.versioning.create_version("doc_1", "v1 body", "first")
        with pytest.raises(VersionNotFoundError) as exc:
            self.versioning.get_version("doc_1", "9.9.9")
        assert "9.9.9" in str(exc.value)

    def test_rollback(self) -> None:
        self.versioning.create_version("doc_1", "v1 body", "first")
        self.versioning.create_version("doc_1", "v2 body", "second")
        rolled_back = self.versioning.rollback("doc_1", "0.1.0")
        assert rolled_back.body == "v1 body"
        assert rolled_back.version == "0.3.0"

    def test_get_latest_version(self) -> None:
        self.versioning.create_version("doc_1", "v1 body", "first")
        self.versioning.create_version("doc_1", "v2 body", "second")
        latest = self.versioning.get_latest_version("doc_1")
        assert latest.body == "v2 body"
        assert latest.version == "0.2.0"

    def test_get_latest_not_found(self) -> None:
        with pytest.raises(ContentNotFoundError):
            self.versioning.get_latest_version("missing")

    def test_diff_versions(self) -> None:
        self.versioning.create_version("doc_1", "line1\nline2\n", "first")
        self.versioning.create_version("doc_1", "line1\nline3\n", "second")
        diff = self.versioning.diff_versions("doc_1", "0.1.0", "0.2.0")
        assert any("-line2" in line for line in diff)
        assert any("+line3" in line for line in diff)

    def test_diff_versions_not_found(self) -> None:
        self.versioning.create_version("doc_1", "body", "first")
        with pytest.raises(VersionNotFoundError):
            self.versioning.diff_versions("doc_1", "0.1.0", "9.9.9")

    def test_max_versions_enforced(self) -> None:
        v = ContentVersioning(
            config=type("Config", (), {"max_versions_per_item": 2, "enable_versioning": True})()
        )
        v.create_version("doc_1", "v1", "first")
        v.create_version("doc_1", "v2", "second")
        v.create_version("doc_1", "v3", "third")
        versions = v.list_versions("doc_1")
        assert len(versions) == 2
        assert versions[-1].body == "v3"
