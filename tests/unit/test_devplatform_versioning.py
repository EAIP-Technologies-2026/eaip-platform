"""Tests for :mod:`eaip.devplatform.versioning`."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from eaip.devplatform.events import ApiVersionDeprecated, ApiVersionRegistered, ApiVersionSunset
from eaip.devplatform.exceptions import VersionNotFoundError
from eaip.devplatform.models import ApiVersion, VersionStatus
from eaip.devplatform.versioning import ApiVersionManager


@pytest.fixture
def manager() -> ApiVersionManager:
    return ApiVersionManager()


@pytest.fixture
def sample_version() -> ApiVersion:
    return ApiVersion(id="v1", version_string="1.0.0")


@pytest.fixture
def populated_manager(manager: ApiVersionManager) -> ApiVersionManager:
    manager.register_version(
        ApiVersion(id="v1", version_string="1.0.0", released_at=datetime(2024, 1, 1, tzinfo=UTC))
    )
    manager.register_version(
        ApiVersion(id="v2", version_string="2.0.0", released_at=datetime(2024, 6, 1, tzinfo=UTC))
    )
    manager.register_version(
        ApiVersion(id="v3", version_string="3.0.0", released_at=datetime(2025, 1, 1, tzinfo=UTC))
    )
    return manager


class TestApiVersionManager:
    def test_register_version(self, manager: ApiVersionManager) -> None:
        v = ApiVersion(id="v1", version_string="1.0.0")
        result = manager.register_version(v)
        assert result.version_string == "1.0.0"
        assert manager.list_versions() == (v,)

    def test_register_version_emits_event(self, manager: ApiVersionManager) -> None:
        events: list[ApiVersionRegistered] = []
        manager.on_event(events.append)
        manager.register_version(ApiVersion(id="v1", version_string="1.0.0"))
        assert len(events) == 1
        assert events[0].version_string == "1.0.0"

    def test_get_version(self, manager: ApiVersionManager) -> None:
        v = ApiVersion(id="v1", version_string="1.0.0")
        manager.register_version(v)
        result = manager.get_version("1.0.0")
        assert result == v

    def test_get_version_not_found(self, manager: ApiVersionManager) -> None:
        with pytest.raises(VersionNotFoundError):
            manager.get_version("nonexistent")

    def test_list_versions_empty(self, manager: ApiVersionManager) -> None:
        assert manager.list_versions() == ()

    def test_list_versions(self, populated_manager: ApiVersionManager) -> None:
        versions = populated_manager.list_versions()
        assert len(versions) == 3

    async def test_deprecate_version(self, manager: ApiVersionManager) -> None:
        v = ApiVersion(id="v1", version_string="1.0.0")
        manager.register_version(v)
        result = await manager.deprecate_version("1.0.0")
        assert result.status is VersionStatus.DEPRECATED

    async def test_deprecate_version_emits_event(self, manager: ApiVersionManager) -> None:
        manager.register_version(ApiVersion(id="v1", version_string="1.0.0"))
        events: list[ApiVersionDeprecated] = []
        manager.on_event(events.append)
        await manager.deprecate_version("1.0.0")
        assert len(events) == 1
        assert events[0].version_string == "1.0.0"

    async def test_deprecate_version_not_found(self, manager: ApiVersionManager) -> None:
        with pytest.raises(VersionNotFoundError):
            await manager.deprecate_version("nonexistent")

    async def test_sunset_version(self, manager: ApiVersionManager) -> None:
        v = ApiVersion(id="v1", version_string="1.0.0")
        manager.register_version(v)
        result = await manager.sunset_version("1.0.0")
        assert result.status is VersionStatus.SUNSET

    async def test_sunset_version_emits_event(self, manager: ApiVersionManager) -> None:
        manager.register_version(ApiVersion(id="v1", version_string="1.0.0"))
        events: list[ApiVersionSunset] = []
        manager.on_event(events.append)
        await manager.sunset_version("1.0.0")
        assert len(events) == 1
        assert events[0].version_string == "1.0.0"

    async def test_sunset_version_not_found(self, manager: ApiVersionManager) -> None:
        with pytest.raises(VersionNotFoundError):
            await manager.sunset_version("nonexistent")

    def test_get_latest_version(self, populated_manager: ApiVersionManager) -> None:
        latest = populated_manager.get_latest_version()
        assert latest is not None
        assert latest.version_string == "3.0.0"

    def test_get_latest_version_empty(self, manager: ApiVersionManager) -> None:
        assert manager.get_latest_version() is None

    def test_resolve_version_specific(self, populated_manager: ApiVersionManager) -> None:
        resolved = populated_manager.resolve_version("1.0.0")
        assert resolved.version_string == "1.0.0"

    def test_resolve_version_fallback(self, populated_manager: ApiVersionManager) -> None:
        resolved = populated_manager.resolve_version(None)
        assert resolved.version_string == "3.0.0"

    def test_resolve_version_not_found(self, manager: ApiVersionManager) -> None:
        with pytest.raises(VersionNotFoundError):
            manager.resolve_version("nonexistent")

    def test_resolve_version_no_versions(self, manager: ApiVersionManager) -> None:
        with pytest.raises(VersionNotFoundError):
            manager.resolve_version(None)
