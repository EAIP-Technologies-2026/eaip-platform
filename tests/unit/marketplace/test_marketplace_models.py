from __future__ import annotations

from datetime import datetime

import pydantic
import pytest

from eaip.marketplace.models import (
    MarketplacePackage,
    PackageInstallation,
    PackageStatus,
    PackageType,
    PackageVersion,
)


class TestPackageType:
    def test_values(self) -> None:
        assert PackageType.AGENT.value == "agent"
        assert PackageType.TOOL.value == "tool"
        assert PackageType.PLUGIN.value == "plugin"
        assert PackageType.TEMPLATE.value == "template"
        assert PackageType.ADAPTER.value == "adapter"

    def test_is_str_enum(self) -> None:
        assert PackageType("agent") is PackageType.AGENT


class TestPackageStatus:
    def test_values(self) -> None:
        assert PackageStatus.DRAFT.value == "draft"
        assert PackageStatus.PUBLISHED.value == "published"
        assert PackageStatus.DEPRECATED.value == "deprecated"
        assert PackageStatus.ARCHIVED.value == "archived"

    def test_is_str_enum(self) -> None:
        assert PackageStatus("published") is PackageStatus.PUBLISHED


class TestMarketplacePackage:
    def test_defaults(self) -> None:
        pkg = MarketplacePackage(
            package_id="pkg-1",
            name="test-agent",
            type=PackageType.AGENT,
            version="1.0.0",
            description="A test agent",
            author="developer",
        )
        assert pkg.package_id == "pkg-1"
        assert pkg.name == "test-agent"
        assert pkg.type is PackageType.AGENT
        assert pkg.version == "1.0.0"
        assert pkg.description == "A test agent"
        assert pkg.author == "developer"
        assert pkg.dependencies == ()
        assert pkg.tags == ()
        assert pkg.status is PackageStatus.DRAFT
        assert isinstance(pkg.created_at, datetime)
        assert isinstance(pkg.updated_at, datetime)
        assert pkg.downloads == 0
        assert pkg.rating == 0.0
        assert pkg.metadata == {}

    def test_frozen(self) -> None:
        pkg = MarketplacePackage(
            package_id="pkg-1",
            name="test-agent",
            type=PackageType.AGENT,
            version="1.0.0",
            description="A test agent",
            author="developer",
        )
        with pytest.raises(pydantic.ValidationError):
            pkg.name = "modified"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            MarketplacePackage(
                package_id="pkg-1",
                name="test-agent",
                type=PackageType.AGENT,
                version="1.0.0",
                description="A test agent",
                author="developer",
                unknown="x",  # type: ignore[call-arg]
            )

    def test_with_dependencies_and_tags(self) -> None:
        pkg = MarketplacePackage(
            package_id="pkg-1",
            name="test-agent",
            type=PackageType.PLUGIN,
            version="2.0.0",
            description="A test plugin",
            author="developer",
            dependencies=("dep-1", "dep-2"),
            tags=("ai", "nlp"),
            status=PackageStatus.PUBLISHED,
        )
        assert pkg.dependencies == ("dep-1", "dep-2")
        assert pkg.tags == ("ai", "nlp")
        assert pkg.status is PackageStatus.PUBLISHED

    def test_with_metadata(self) -> None:
        pkg = MarketplacePackage(
            package_id="pkg-1",
            name="test-agent",
            type=PackageType.TOOL,
            version="1.0.0",
            description="A test tool",
            author="developer",
            metadata={"key": "value"},
        )
        assert pkg.metadata["key"] == "value"

    def test_invalid_type(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            MarketplacePackage(
                package_id="pkg-1",
                name="test",
                type="invalid",  # type: ignore[arg-type]
                version="1.0.0",
                description="desc",
                author="dev",
            )

    def test_invalid_status(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            MarketplacePackage(
                package_id="pkg-1",
                name="test",
                type=PackageType.AGENT,
                version="1.0.0",
                description="desc",
                author="dev",
                status="unknown",  # type: ignore[arg-type]
            )


class TestPackageVersion:
    def test_defaults(self) -> None:
        ver = PackageVersion(
            package_id="pkg-1",
            version="1.0.0",
            semver_range=">=1.0.0",
            changelog="Initial release",
            checksum="abc123",
            size_bytes=1024,
        )
        assert ver.package_id == "pkg-1"
        assert ver.version == "1.0.0"
        assert ver.semver_range == ">=1.0.0"
        assert ver.changelog == "Initial release"
        assert ver.checksum == "abc123"
        assert ver.size_bytes == 1024
        assert isinstance(ver.created_at, datetime)
        assert ver.is_compatible is True

    def test_frozen(self) -> None:
        ver = PackageVersion(
            package_id="pkg-1",
            version="1.0.0",
            semver_range=">=1.0.0",
            changelog="Initial release",
            checksum="abc123",
            size_bytes=1024,
        )
        with pytest.raises(pydantic.ValidationError):
            ver.version = "2.0.0"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            PackageVersion(
                package_id="pkg-1",
                version="1.0.0",
                semver_range=">=1.0.0",
                changelog="Initial release",
                checksum="abc123",
                size_bytes=1024,
                unknown="x",  # type: ignore[call-arg]
            )

    def test_not_compatible(self) -> None:
        ver = PackageVersion(
            package_id="pkg-1",
            version="1.0.0",
            semver_range=">=1.0.0",
            changelog="Initial release",
            checksum="abc123",
            size_bytes=1024,
            is_compatible=False,
        )
        assert ver.is_compatible is False


class TestPackageInstallation:
    def test_defaults(self) -> None:
        inst = PackageInstallation(
            installation_id="inst-1",
            package_id="pkg-1",
            version="1.0.0",
            installed_by="user-1",
            status="active",
        )
        assert inst.installation_id == "inst-1"
        assert inst.package_id == "pkg-1"
        assert inst.version == "1.0.0"
        assert inst.installed_by == "user-1"
        assert inst.status == "active"
        assert isinstance(inst.installed_at, datetime)
        assert inst.metadata == {}

    def test_frozen(self) -> None:
        inst = PackageInstallation(
            installation_id="inst-1",
            package_id="pkg-1",
            version="1.0.0",
            installed_by="user-1",
            status="active",
        )
        with pytest.raises(pydantic.ValidationError):
            inst.status = "uninstalled"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            PackageInstallation(
                installation_id="inst-1",
                package_id="pkg-1",
                version="1.0.0",
                installed_by="user-1",
                status="active",
                unknown="x",  # type: ignore[call-arg]
            )

    def test_with_metadata(self) -> None:
        inst = PackageInstallation(
            installation_id="inst-1",
            package_id="pkg-1",
            version="1.0.0",
            installed_by="user-1",
            status="active",
            metadata={"env": "production"},
        )
        assert inst.metadata["env"] == "production"
