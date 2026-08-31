"""Domain events raised by the marketplace package."""

from __future__ import annotations

from typing import ClassVar

from eaip.events.event import DomainEvent


class PackagePublished(DomainEvent):
    """Published when a package is published."""

    event_type: ClassVar[str] = "eaip.marketplace.package_published"

    package_id: str
    name: str
    type: str
    version: str


class PackageInstalled(DomainEvent):
    """Published when a package is installed."""

    event_type: ClassVar[str] = "eaip.marketplace.package_installed"

    package_id: str
    version: str
    installation_id: str


class PackageUninstalled(DomainEvent):
    """Published when a package is uninstalled."""

    event_type: ClassVar[str] = "eaip.marketplace.package_uninstalled"

    package_id: str
    installation_id: str
    reason: str = ""


class PackageUpdated(DomainEvent):
    """Published when a package is updated."""

    event_type: ClassVar[str] = "eaip.marketplace.package_updated"

    package_id: str
    from_version: str
    to_version: str


class PackageDeprecated(DomainEvent):
    """Published when a package is deprecated."""

    event_type: ClassVar[str] = "eaip.marketplace.package_deprecated"

    package_id: str
    reason: str = ""


class PackageDownloaded(DomainEvent):
    """Published when a package is downloaded."""

    event_type: ClassVar[str] = "eaip.marketplace.package_downloaded"

    package_id: str
    version: str
    downloader: str
