"""Tests for :mod:`eaip.sdk.manager`."""

from __future__ import annotations

import pytest

from eaip.sdk.exceptions import BuildError, SdkNotFoundError
from eaip.sdk.manager import SdkManager
from eaip.sdk.models import BuildStatus, SdkStatus


class TestSdkManager:
    def test_create_sdk(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        assert sdk.id.startswith("sdk-")
        assert sdk.name == "TestSDK"
        assert sdk.status is SdkStatus.DRAFT

    def test_get_sdk(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        retrieved = mgr.get_sdk(sdk.id)
        assert retrieved.id == sdk.id

    def test_get_sdk_not_found(self) -> None:
        mgr = SdkManager()
        with pytest.raises(SdkNotFoundError):
            mgr.get_sdk("nonexistent")

    def test_update_sdk(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        updated = mgr.update_sdk(sdk.id, description="Updated description")
        assert updated.description == "Updated description"
        assert updated.updated_at >= sdk.updated_at

    def test_delete_sdk(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        mgr.delete_sdk(sdk.id)
        with pytest.raises(SdkNotFoundError):
            mgr.get_sdk(sdk.id)

    def test_delete_sdk_not_found(self) -> None:
        mgr = SdkManager()
        with pytest.raises(SdkNotFoundError):
            mgr.delete_sdk("nonexistent")

    def test_list_sdks(self) -> None:
        mgr = SdkManager()
        mgr.create_sdk(name="PySDK", language="python", version="1.0.0")
        mgr.create_sdk(name="JSSDK", language="javascript", version="1.0.0")
        mgr.create_sdk(name="PySDK2", language="python", version="2.0.0")
        all_sdks = mgr.list_sdks()
        assert len(all_sdks) == 3
        py_sdks = mgr.list_sdks(language="python")
        assert len(py_sdks) == 2

    def test_list_sdks_by_status(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        mgr._sdks[sdk.id] = sdk.model_copy(update={"status": SdkStatus.PUBLISHED})
        published = mgr.list_sdks(status=SdkStatus.PUBLISHED)
        assert len(published) == 1


class TestEndpoints:
    def test_register_endpoint(self) -> None:
        mgr = SdkManager()
        ep = mgr.register_endpoint(path="/v1/users", method="GET", description="List users")
        assert ep.id.startswith("ep-")
        assert ep.method == "GET"
        assert ep.path == "/v1/users"

    def test_list_endpoints_all(self) -> None:
        mgr = SdkManager()
        mgr.register_endpoint(path="/v1/users", method="GET")
        mgr.register_endpoint(path="/v1/items", method="POST")
        eps = mgr.list_endpoints()
        assert len(eps) == 2

    def test_list_endpoints_by_sdk(self) -> None:
        mgr = SdkManager()
        ep = mgr.register_endpoint(path="/v1/users", method="GET")
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0", endpoints=(ep.id,))
        eps = mgr.list_endpoints(sdk_id=sdk.id)
        assert len(eps) == 1


class TestBuilds:
    def test_create_build(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        build = mgr.create_build(sdk.id, version="1.0.0")
        assert build.id.startswith("bld-")
        assert build.status is BuildStatus.PENDING
        assert build.sdk_id == sdk.id

    def test_create_build_nonexistent_sdk(self) -> None:
        mgr = SdkManager()
        with pytest.raises(SdkNotFoundError):
            mgr.create_build("nonexistent", version="1.0.0")

    async def test_get_build(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        build = mgr.create_build(sdk.id, version="1.0.0")
        retrieved = await mgr.get_build(build.id)
        assert retrieved.id == build.id

    async def test_get_build_not_found(self) -> None:
        mgr = SdkManager()
        with pytest.raises(BuildError):
            await mgr.get_build("nonexistent")

    async def test_list_builds(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        mgr.create_build(sdk.id, version="1.0.0")
        mgr.create_build(sdk.id, version="1.0.1")
        builds = await mgr.list_builds(sdk.id)
        assert len(builds) == 2

    async def test_list_builds_limit(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        for _ in range(5):
            mgr.create_build(sdk.id, version="1.0.0")
        builds = await mgr.list_builds(sdk.id, limit=3)
        assert len(builds) == 3

    async def test_publish_sdk(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        published = await mgr.publish_sdk(sdk.id, version="1.0.0")
        assert published.status is SdkStatus.PUBLISHED

    async def test_publish_deprecated_sdk_fails(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        await mgr.deprecate_sdk(sdk.id, version="1.0.0")
        with pytest.raises(BuildError):
            await mgr.publish_sdk(sdk.id, version="1.0.0")

    async def test_deprecate_sdk(self) -> None:
        mgr = SdkManager()
        sdk = mgr.create_sdk(name="TestSDK", language="python", version="1.0.0")
        deprecated = await mgr.deprecate_sdk(sdk.id, version="1.0.0")
        assert deprecated.status is SdkStatus.DEPRECATED
