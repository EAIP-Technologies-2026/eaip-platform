"""API version management — registration, deprecation, sunset, and resolution."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.devplatform.events import ApiVersionDeprecated, ApiVersionRegistered, ApiVersionSunset
from eaip.devplatform.exceptions import VersionNotFoundError
from eaip.devplatform.models import ApiVersion, VersionStatus


class ApiVersionManager:
    """Manages the lifecycle of public API versions."""

    def __init__(self) -> None:
        """Initialize ApiVersionManager with an empty version store."""
        self._versions: dict[str, ApiVersion] = {}
        self._event_handlers: list[Any] = []

    def on_event(self, handler: Any) -> None:
        """Register an event handler for version lifecycle events.

        Args:
            handler: A callable that accepts event instances.
        """
        self._event_handlers.append(handler)

    def _emit(self, event: Any) -> None:
        """Emit an event to all registered handlers.

        Args:
            event: The event instance to emit.
        """
        for handler in self._event_handlers:
            handler(event)

    def register_version(self, version: ApiVersion) -> ApiVersion:
        """Register a new API version.

        Args:
            version: The ApiVersion to register.

        Returns:
            The registered ApiVersion.
        """
        self._versions[version.version_string] = version
        self._emit(
            ApiVersionRegistered(version_id=version.id, version_string=version.version_string)
        )
        return version

    def get_version(self, version_string: str) -> ApiVersion:
        """Get version details by version string.

        Args:
            version_string: The version string to look up.

        Returns:
            The matching ApiVersion.

        Raises:
            VersionNotFoundError: If the version is not found.
        """
        version = self._versions.get(version_string)
        if version is None:
            raise VersionNotFoundError(
                f"API version {version_string!r} not found",
                context={"version_string": version_string},
            )
        return version

    def list_versions(self) -> tuple[ApiVersion, ...]:
        """List all registered API versions.

        Returns:
            A tuple of all registered ApiVersion instances.
        """
        return tuple(self._versions.values())

    async def deprecate_version(
        self, version_string: str, sunset_at: datetime | None = None
    ) -> ApiVersion:
        """Deprecate an API version.

        Args:
            version_string: The version string to deprecate.
            sunset_at: Optional datetime when the version will be sunset.

        Returns:
            The updated ApiVersion.

        Raises:
            VersionNotFoundError: If the version is not found.
        """
        version = self._versions.get(version_string)
        if version is None:
            raise VersionNotFoundError(
                f"API version {version_string!r} not found",
                context={"version_string": version_string},
            )
        updated = ApiVersion(
            id=version.id,
            version_string=version.version_string,
            status=VersionStatus.DEPRECATED,
            released_at=version.released_at,
            sunset_at=sunset_at or version.sunset_at,
            changelog=version.changelog,
            migration_guide=version.migration_guide,
            metadata=version.metadata,
        )
        self._versions[version_string] = updated
        self._emit(
            ApiVersionDeprecated(
                version_id=version.id,
                version_string=version_string,
                sunset_at=sunset_at,
            )
        )
        return updated

    async def sunset_version(self, version_string: str) -> ApiVersion:
        """Sunset / retire an API version.

        Args:
            version_string: The version string to sunset.

        Returns:
            The updated ApiVersion.

        Raises:
            VersionNotFoundError: If the version is not found.
        """
        version = self._versions.get(version_string)
        if version is None:
            raise VersionNotFoundError(
                f"API version {version_string!r} not found",
                context={"version_string": version_string},
            )
        updated = ApiVersion(
            id=version.id,
            version_string=version.version_string,
            status=VersionStatus.SUNSET,
            released_at=version.released_at,
            sunset_at=version.sunset_at,
            changelog=version.changelog,
            migration_guide=version.migration_guide,
            metadata=version.metadata,
        )
        self._versions[version_string] = updated
        self._emit(ApiVersionSunset(version_id=version.id, version_string=version_string))
        return updated

    def get_latest_version(self) -> ApiVersion | None:
        """Get the latest active API version.

        Returns:
            The most recent active ApiVersion, or None if no active version exists.
        """
        active = [v for v in self._versions.values() if v.status is VersionStatus.ACTIVE]
        if not active:
            return None
        return max(active, key=lambda v: v.released_at)

    def resolve_version(self, requested_version: str | None) -> ApiVersion:
        """Resolve a requested version with fallback to the latest active version.

        Args:
            requested_version: The requested version string, or None.

        Returns:
            The resolved ApiVersion.

        Raises:
            VersionNotFoundError: If the requested version is not found and no
                latest active version exists.
        """
        if requested_version:
            version = self._versions.get(requested_version)
            if version is None:
                raise VersionNotFoundError(
                    f"API version {requested_version!r} not found",
                    context={"version_string": requested_version},
                )
            return version
        latest = self.get_latest_version()
        if latest is None:
            raise VersionNotFoundError(
                "No API versions registered",
                context={"version_string": requested_version},
            )
        return latest


__all__ = ["ApiVersionManager"]
