from __future__ import annotations

import pytest

from eaip.filestore.asset_manager import AssetManager
from eaip.filestore.exceptions import (
    DuplicateFileError,
    FileNotFoundError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from eaip.filestore.models import FileAsset, FileConfig


class _Fixture:
    def __init__(self) -> None:
        self.mgr = AssetManager()


@pytest.fixture
def fixture() -> _Fixture:
    return _Fixture()


class TestAssetManager:
    @pytest.mark.asyncio
    async def test_upload(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(
            b"file content", "test.txt", tags=("docs",), content_type="text/plain"
        )
        assert asset.name == "test.txt"
        assert asset.tags == ("docs",)
        assert asset.size_bytes == len(b"file content")
        assert asset.version == 1

    @pytest.mark.asyncio
    async def test_upload_default_content_type(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"data", "data.bin")
        assert asset.content_type == "application/octet-stream"

    @pytest.mark.asyncio
    async def test_upload_unsupported_type(self, fixture: _Fixture) -> None:
        cfg = FileConfig(allowed_types=("image/png",))
        mgr = AssetManager(config=cfg)
        with pytest.raises(UnsupportedFileTypeError):
            await mgr.upload(b"data", "test.exe", content_type="application/x-msdownload")

    @pytest.mark.asyncio
    async def test_upload_too_large(self, fixture: _Fixture) -> None:
        cfg = FileConfig(max_upload_size_mb=1)
        mgr = AssetManager(config=cfg)
        large = b"x" * (2 * 1024 * 1024)
        with pytest.raises(FileTooLargeError):
            await mgr.upload(large, "large.bin")

    @pytest.mark.asyncio
    async def test_upload_duplicate_detection(self, fixture: _Fixture) -> None:
        await fixture.mgr.upload(b"same content", "file1.txt")
        with pytest.raises(DuplicateFileError):
            await fixture.mgr.upload(b"same content", "file2.txt")

    @pytest.mark.asyncio
    async def test_upload_dedup_disabled(self, fixture: _Fixture) -> None:
        cfg = FileConfig(enable_deduplication=False)
        mgr = AssetManager(config=cfg)
        await mgr.upload(b"same", "f1.txt")
        asset2 = await mgr.upload(b"same", "f2.txt")
        assert asset2 is not None

    @pytest.mark.asyncio
    async def test_download(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"content", "file.txt")
        data = await fixture.mgr.download(asset.id)
        assert isinstance(data, bytes)

    @pytest.mark.asyncio
    async def test_download_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(FileNotFoundError):
            await fixture.mgr.download("nonexistent")

    @pytest.mark.asyncio
    async def test_download_with_version(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"content", "file.txt")
        data = await fixture.mgr.download(asset.id, version=1)
        assert isinstance(data, bytes)

    @pytest.mark.asyncio
    async def test_download_version_not_found(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"content", "file.txt")
        with pytest.raises(FileNotFoundError):
            await fixture.mgr.download(asset.id, version=999)

    @pytest.mark.asyncio
    async def test_delete(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"content", "file.txt")
        deleted = await fixture.mgr.delete(asset.id)
        assert deleted.status == "deleted"

    @pytest.mark.asyncio
    async def test_delete_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(FileNotFoundError):
            await fixture.mgr.delete("nonexistent")

    @pytest.mark.asyncio
    async def test_get(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"content", "file.txt")
        found = await fixture.mgr.get(asset.id)
        assert found.id == asset.id

    @pytest.mark.asyncio
    async def test_get_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(FileNotFoundError):
            await fixture.mgr.get("nonexistent")

    def test_list_items_empty(self, fixture: _Fixture) -> None:
        assert fixture.mgr.list_items() == []

    @pytest.mark.asyncio
    async def test_list_items(self, fixture: _Fixture) -> None:
        await fixture.mgr.upload(b"a", "a.txt")
        await fixture.mgr.upload(b"b", "b.txt")
        assert len(fixture.mgr.list_items()) == 2

    @pytest.mark.asyncio
    async def test_list_items_filter_folder(self, fixture: _Fixture) -> None:
        await fixture.mgr.upload(b"a", "a.txt")
        result = fixture.mgr.list_items(folder="/storage/")
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_list_items_filter_tags(self, fixture: _Fixture) -> None:
        await fixture.mgr.upload(b"a", "a.txt", tags=("important",))
        await fixture.mgr.upload(b"b", "b.txt", tags=("trash",))
        result = fixture.mgr.list_items(tags=("important",))
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search(self, fixture: _Fixture) -> None:
        await fixture.mgr.upload(b"a", "important_doc.pdf")
        results = await fixture.mgr.search("important")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_no_results(self, fixture: _Fixture) -> None:
        results = await fixture.mgr.search("nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_create_version(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"v1", "file.txt")
        version = await fixture.mgr.create_version(asset.id, b"v2 content", "updated")
        assert version.version == 2
        assert version.change_log == "updated"

    @pytest.mark.asyncio
    async def test_create_version_disabled(self, fixture: _Fixture) -> None:
        cfg = FileConfig(enable_versioning=False)
        mgr = AssetManager(config=cfg)
        asset = await mgr.upload(b"v1", "file.txt")
        with pytest.raises(FileTooLargeError):
            await mgr.create_version(asset.id, b"v2")

    @pytest.mark.asyncio
    async def test_create_version_max_versions(self, fixture: _Fixture) -> None:
        cfg = FileConfig(max_versions=2)
        mgr = AssetManager(config=cfg)
        asset = await mgr.upload(b"v1", "file.txt")
        await mgr.create_version(asset.id, b"v2")
        with pytest.raises(FileTooLargeError):
            await mgr.create_version(asset.id, b"v3")

    @pytest.mark.asyncio
    async def test_get_versions(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"v1", "file.txt")
        await fixture.mgr.create_version(asset.id, b"v2")
        versions = await fixture.mgr.get_versions(asset.id)
        assert len(versions) == 2

    @pytest.mark.asyncio
    async def test_get_versions_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(FileNotFoundError):
            await fixture.mgr.get_versions("nonexistent")

    @pytest.mark.asyncio
    async def test_get_latest_version(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"v1", "file.txt")
        await fixture.mgr.create_version(asset.id, b"v2")
        latest = await fixture.mgr.get_latest_version(asset.id)
        assert latest.version == 2

    @pytest.mark.asyncio
    async def test_get_latest_version_no_versions(self, fixture: _Fixture) -> None:
        mgr = AssetManager()
        mgr._assets["a1"] = _make_dummy_asset()
        with pytest.raises(FileNotFoundError):
            await mgr.get_latest_version("a1")

    @pytest.mark.asyncio
    async def test_duplicate(self, fixture: _Fixture) -> None:
        asset = await fixture.mgr.upload(b"content", "original.txt")
        dup = await fixture.mgr.duplicate(asset.id)
        assert dup.id != asset.id
        assert "copy" in dup.name

    @pytest.mark.asyncio
    async def test_duplicate_not_found(self, fixture: _Fixture) -> None:
        with pytest.raises(FileNotFoundError):
            await fixture.mgr.duplicate("nonexistent")

    def test_update_config(self, fixture: _Fixture) -> None:
        cfg = fixture.mgr.update_config(max_upload_size_mb=500)
        assert cfg.max_upload_size_mb == 500
        assert fixture.mgr.config.max_upload_size_mb == 500


def _make_dummy_asset() -> object:
    return FileAsset(
        id="a1",
        name="dummy",
        original_filename="dummy.txt",
        content_type="text/plain",
        size_bytes=10,
        storage_path="/s/dummy",
    )
