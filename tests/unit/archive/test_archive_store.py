"""Tests for archive storage backends."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from eaip.archive.store import ArchiveStore, LocalArchiveStore, S3ArchiveStore


class TestArchiveStore:
    def test_abstract_methods(self) -> None:
        method_names = {"store", "retrieve", "delete", "exists"}
        for name in method_names:
            assert hasattr(ArchiveStore, name)


class TestLocalArchiveStore:
    @pytest.fixture
    def store(self) -> LocalArchiveStore:
        tmp = tempfile.mkdtemp()
        return LocalArchiveStore(base_path=tmp)

    def test_store_and_retrieve(self, store: LocalArchiveStore) -> None:
        store.store("rec_1", b"hello world")
        data = store.retrieve("rec_1")
        assert data == b"hello world"

    def test_exists(self, store: LocalArchiveStore) -> None:
        assert store.exists("rec_1") is False
        store.store("rec_1", b"data")
        assert store.exists("rec_1") is True

    def test_delete(self, store: LocalArchiveStore) -> None:
        store.store("rec_1", b"data")
        store.delete("rec_1")
        assert store.exists("rec_1") is False

    def test_delete_missing(self, store: LocalArchiveStore) -> None:
        store.delete("nonexistent")

    def test_different_records(self, store: LocalArchiveStore) -> None:
        store.store("r1", b"data1")
        store.store("r2", b"data2")
        assert store.retrieve("r1") == b"data1"
        assert store.retrieve("r2") == b"data2"

    def test_base_path_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "archive_sub"
            store = LocalArchiveStore(base_path=str(path))
            assert path.exists() is True
            store.store("r1", b"data")
            assert store.retrieve("r1") == b"data"


class TestS3ArchiveStore:
    @pytest.fixture
    def store(self) -> S3ArchiveStore:
        return S3ArchiveStore(bucket="test-bucket", prefix="archive/")

    def test_store_not_implemented(self, store: S3ArchiveStore) -> None:
        with pytest.raises(NotImplementedError):
            store.store("r1", b"data")

    def test_retrieve_not_implemented(self, store: S3ArchiveStore) -> None:
        with pytest.raises(NotImplementedError):
            store.retrieve("r1")

    def test_delete_not_implemented(self, store: S3ArchiveStore) -> None:
        with pytest.raises(NotImplementedError):
            store.delete("r1")

    def test_exists_not_implemented(self, store: S3ArchiveStore) -> None:
        with pytest.raises(NotImplementedError):
            store.exists("r1")
