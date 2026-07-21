"""Release management — create releases, promote between environments, track versions."""

from __future__ import annotations

from eaip.deploy.models import Release
from eaip.shared.time import utc_now


class ReleaseManager:
    """Manages the release lifecycle — creation, promotion, and version tracking."""

    def __init__(self) -> None:
        """Initialize the release manager with an empty release store."""
        self._releases: dict[str, Release] = {}

    def create_release(
        self,
        release_id: str,
        version: str,
        name: str,
        description: str | None = None,
    ) -> Release:
        """Create a new release and store it.

        Args:
            release_id: Unique identifier for the release.
            version: Semantic version string.
            name: Human-readable release name.
            description: Optional description of the release.

        Returns:
            The newly created Release.
        """
        release = Release(
            release_id=release_id,
            version=version,
            name=name,
            description=description,
        )
        self._releases[release_id] = release
        return release

    def get_release(self, release_id: str) -> Release | None:
        """Retrieve a release by its identifier.

        Args:
            release_id: Unique identifier for the release.

        Returns:
            The Release if found, or None.
        """
        return self._releases.get(release_id)

    def promote_release(
        self,
        release_id: str,
        from_environment: str,
        to_environment: str,
    ) -> Release | None:
        """Promote a release from one environment to another.

        Only releases with status ``testing`` or ``deployed`` can be promoted.

        Args:
            release_id: Unique identifier for the release.
            from_environment: Source environment name.
            to_environment: Target environment name.

        Returns:
            The promoted Release, or None if not found or not promotable.
        """
        release = self._releases.get(release_id)
        if release is None:
            return None
        if release.status not in ("testing", "deployed"):
            return None
        if from_environment not in ("dev", "staging", "prod"):
            return None
        if to_environment not in ("dev", "staging", "prod"):
            return None
        promoted = Release(
            release_id=release.release_id,
            version=release.version,
            name=release.name,
            description=release.description,
            artifacts=release.artifacts,
            status=release.status,
            created_at=release.created_at,
            deployed_at=utc_now(),
            metadata=release.metadata,
        )
        self._releases[release_id] = promoted
        return promoted

    def update_status(self, release_id: str, status: str) -> Release | None:
        """Update the status of an existing release.

        Args:
            release_id: Unique identifier for the release.
            status: New status value.

        Returns:
            The updated Release, or None if not found.
        """
        release = self._releases.get(release_id)
        if release is None:
            return None
        deployed_at = release.deployed_at
        if status == "deployed":
            deployed_at = utc_now()
        updated = Release(
            release_id=release.release_id,
            version=release.version,
            name=release.name,
            description=release.description,
            artifacts=release.artifacts,
            status=status,
            created_at=release.created_at,
            deployed_at=deployed_at,
            metadata=release.metadata,
        )
        self._releases[release_id] = updated
        return updated

    @property
    def releases(self) -> dict[str, Release]:
        """Return a copy of all tracked releases."""
        return dict(self._releases)


__all__ = ["ReleaseManager"]
