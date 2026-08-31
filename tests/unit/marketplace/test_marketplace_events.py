from __future__ import annotations

import pydantic
import pytest

from eaip.marketplace.events import (
    PackageDeprecated,
    PackageDownloaded,
    PackageInstalled,
    PackagePublished,
    PackageUninstalled,
    PackageUpdated,
)


class TestMarketplaceEvents:
    def test_package_published(self) -> None:
        event = PackagePublished(
            package_id="pkg-1", name="test-package", type="agent", version="1.0.0"
        )
        assert event.event_type == "eaip.marketplace.package_published"
        assert event.package_id == "pkg-1"
        assert event.name == "test-package"
        assert event.type == "agent"
        assert event.version == "1.0.0"

    def test_package_installed(self) -> None:
        event = PackageInstalled(package_id="pkg-1", version="1.0.0", installation_id="inst-1")
        assert event.event_type == "eaip.marketplace.package_installed"
        assert event.package_id == "pkg-1"
        assert event.version == "1.0.0"
        assert event.installation_id == "inst-1"

    def test_package_uninstalled(self) -> None:
        event = PackageUninstalled(package_id="pkg-1", installation_id="inst-1", reason="upgrade")
        assert event.event_type == "eaip.marketplace.package_uninstalled"
        assert event.package_id == "pkg-1"
        assert event.installation_id == "inst-1"
        assert event.reason == "upgrade"

    def test_package_uninstalled_default_reason(self) -> None:
        event = PackageUninstalled(package_id="pkg-1", installation_id="inst-1")
        assert event.reason == ""

    def test_package_updated(self) -> None:
        event = PackageUpdated(package_id="pkg-1", from_version="1.0.0", to_version="2.0.0")
        assert event.event_type == "eaip.marketplace.package_updated"
        assert event.package_id == "pkg-1"
        assert event.from_version == "1.0.0"
        assert event.to_version == "2.0.0"

    def test_package_deprecated(self) -> None:
        event = PackageDeprecated(package_id="pkg-1", reason="no longer maintained")
        assert event.event_type == "eaip.marketplace.package_deprecated"
        assert event.package_id == "pkg-1"
        assert event.reason == "no longer maintained"

    def test_package_deprecated_default_reason(self) -> None:
        event = PackageDeprecated(package_id="pkg-1")
        assert event.reason == ""

    def test_package_downloaded(self) -> None:
        event = PackageDownloaded(package_id="pkg-1", version="1.0.0", downloader="user-1")
        assert event.event_type == "eaip.marketplace.package_downloaded"
        assert event.package_id == "pkg-1"
        assert event.version == "1.0.0"
        assert event.downloader == "user-1"

    def test_frozen(self) -> None:
        event = PackagePublished(
            package_id="pkg-1", name="test-package", type="agent", version="1.0.0"
        )
        with pytest.raises(pydantic.ValidationError):
            event.package_id = "pkg-2"  # type: ignore[misc]
