from __future__ import annotations

import pydantic
import pytest

from eaip.filestore.models import AssetVersion, FileAsset, FileConfig, StorageProvider


class TestFileConfig:
    def test_defaults(self) -> None:
        cfg = FileConfig()
        assert cfg.max_upload_size_mb == 100
        assert cfg.allowed_types == ("*/*",)
        assert cfg.storage_provider == "local"
        assert cfg.enable_versioning is True
        assert cfg.max_versions == 10
        assert cfg.enable_deduplication is True

    def test_frozen(self) -> None:
        cfg = FileConfig()
        with pytest.raises(pydantic.ValidationError):
            cfg.max_upload_size_mb = 200  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            FileConfig(unknown="x")  # type: ignore[call-arg]

    def test_range_validation(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            FileConfig(max_upload_size_mb=0)

    def test_custom_allowed_types(self) -> None:
        cfg = FileConfig(allowed_types=("image/png", "image/jpeg"))
        assert cfg.allowed_types == ("image/png", "image/jpeg")


class TestStorageProvider:
    def test_defaults(self) -> None:
        p = StorageProvider(id="p1", name="local", type="local")
        assert p.id == "p1"
        assert p.type == "local"
        assert p.enabled is True
        assert p.default is False
        assert p.config == {}

    def test_frozen(self) -> None:
        p = StorageProvider(id="p1", name="local", type="local")
        with pytest.raises(pydantic.ValidationError):
            p.enabled = False  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            StorageProvider(id="p1", name="local", type="local", unknown="x")  # type: ignore[call-arg]

    def test_invalid_type(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            StorageProvider(id="p1", name="x", type="ftp")

    def test_all_types(self) -> None:
        for t in ("local", "s3", "gcs", "azure"):
            p = StorageProvider(id="p1", name=t, type=t)
            assert p.type == t

    def test_with_config(self) -> None:
        p = StorageProvider(
            id="p1", name="aws", type="s3", config={"bucket": "my-bucket"}, default=True
        )
        assert p.config["bucket"] == "my-bucket"
        assert p.default is True


class TestFileAsset:
    def test_defaults(self) -> None:
        asset = FileAsset(
            id="a1",
            name="test.txt",
            original_filename="test.txt",
            content_type="text/plain",
            size_bytes=100,
            storage_path="/s/a1/test.txt",
        )
        assert asset.id == "a1"
        assert asset.version == 1
        assert asset.tags == ()
        assert asset.metadata == {}
        assert asset.status == "active"
        assert asset.hash == ""

    def test_frozen(self) -> None:
        asset = FileAsset(
            id="a1",
            name="t.txt",
            original_filename="t.txt",
            content_type="text/plain",
            size_bytes=10,
            storage_path="/s/a1/t.txt",
        )
        with pytest.raises(pydantic.ValidationError):
            asset.name = "new.txt"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            FileAsset(
                id="a1",
                name="t.txt",
                original_filename="t.txt",
                content_type="text/plain",
                size_bytes=10,
                storage_path="/s/a1/t.txt",
                unknown="x",
            )  # type: ignore[call-arg]

    def test_invalid_status(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            FileAsset(
                id="a1",
                name="t.txt",
                original_filename="t.txt",
                content_type="text/plain",
                size_bytes=10,
                storage_path="/s/a1/t.txt",
                status="invalid",
            )

    def test_negative_size(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            FileAsset(
                id="a1",
                name="t.txt",
                original_filename="t.txt",
                content_type="text/plain",
                size_bytes=-1,
                storage_path="/s/a1/t.txt",
            )

    def test_with_tags(self) -> None:
        asset = FileAsset(
            id="a1",
            name="doc.pdf",
            original_filename="doc.pdf",
            content_type="application/pdf",
            size_bytes=5000,
            storage_path="/s/a1/doc.pdf",
            tags=("important", "report"),
        )
        assert "important" in asset.tags
        assert asset.content_type == "application/pdf"

    def test_archived_status(self) -> None:
        asset = FileAsset(
            id="a1",
            name="old.txt",
            original_filename="old.txt",
            content_type="text/plain",
            size_bytes=10,
            storage_path="/s/a1/old.txt",
            status="archived",
        )
        assert asset.status == "archived"


class TestAssetVersion:
    def test_defaults(self) -> None:
        v = AssetVersion(
            id="v1", asset_id="a1", version=1, size_bytes=100, storage_path="/s/a1/v1", hash="abc"
        )
        assert v.id == "v1"
        assert v.version == 1
        assert v.change_log == ""
        assert v.metadata == {}

    def test_frozen(self) -> None:
        v = AssetVersion(id="v1", asset_id="a1", version=1, size_bytes=100, storage_path="/s/a1/v1")
        with pytest.raises(pydantic.ValidationError):
            v.version = 2  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            AssetVersion(
                id="v1",
                asset_id="a1",
                version=1,
                size_bytes=100,
                storage_path="/s/a1/v1",
                unknown="x",
            )  # type: ignore[call-arg]

    def test_with_metadata(self) -> None:
        v = AssetVersion(
            id="v1",
            asset_id="a1",
            version=2,
            size_bytes=200,
            storage_path="/s/a1/v2",
            change_log="Updated content",
            metadata={"author": "user1"},
        )
        assert v.change_log == "Updated content"
        assert v.metadata["author"] == "user1"
