from __future__ import annotations

import pydantic
import pytest

from eaip.filestore.events import (
    AssetVersionCreated,
    FileConfigUpdated,
    FileDeleted,
    FileDownloaded,
    FileStoreEvent,
    FileUploaded,
)


class TestFilestoreEvents:
    def test_base_event(self) -> None:
        assert FileStoreEvent.event_type == "eaip.filestore.event"

    def test_file_uploaded(self) -> None:
        event = FileUploaded(
            asset_id="a1",
            name="test.txt",
            content_type="text/plain",
            size_bytes=100,
            tags=("docs",),
        )
        assert event.event_type == "eaip.filestore.file.uploaded"
        assert event.asset_id == "a1"
        assert event.name == "test.txt"
        assert event.tags == ("docs",)

    def test_file_uploaded_default_tags(self) -> None:
        event = FileUploaded(
            asset_id="a1", name="test.txt", content_type="text/plain", size_bytes=100
        )
        assert event.tags == ()

    def test_file_downloaded(self) -> None:
        event = FileDownloaded(asset_id="a1", name="test.txt", version=2)
        assert event.event_type == "eaip.filestore.file.downloaded"
        assert event.version == 2

    def test_file_downloaded_default_version(self) -> None:
        event = FileDownloaded(asset_id="a1", name="test.txt")
        assert event.version == 1

    def test_file_deleted(self) -> None:
        event = FileDeleted(asset_id="a1", name="test.txt")
        assert event.event_type == "eaip.filestore.file.deleted"
        assert event.asset_id == "a1"

    def test_asset_version_created(self) -> None:
        event = AssetVersionCreated(asset_id="a1", version=2, size_bytes=200, change_log="Updated")
        assert event.event_type == "eaip.filestore.asset.version_created"
        assert event.change_log == "Updated"

    def test_asset_version_created_defaults(self) -> None:
        event = AssetVersionCreated(asset_id="a1", version=1, size_bytes=100)
        assert event.change_log == ""

    def test_file_config_updated(self) -> None:
        event = FileConfigUpdated(changes={"max_upload_size_mb": 200})
        assert event.event_type == "eaip.filestore.config.updated"
        assert event.changes["max_upload_size_mb"] == 200

    def test_all_events_frozen(self) -> None:
        event = FileUploaded(asset_id="a1", name="t.txt", content_type="text/plain", size_bytes=10)
        with pytest.raises(pydantic.ValidationError):
            event.asset_id = "a2"  # type: ignore[misc]
