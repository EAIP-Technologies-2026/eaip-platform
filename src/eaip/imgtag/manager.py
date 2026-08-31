"""ImageTagManager — create, update, and delete image tags."""

from __future__ import annotations

from eaip.imgtag.events import ManifestPushed, TagCreated, TagDeleted, TagUpdated
from eaip.imgtag.exceptions import TagManagerError, TagNotFoundError
from eaip.imgtag.models import ImageManifest, ImageTag, TagConfig
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ImageTagManager:
    """Central service for managing container image tags."""

    def __init__(self, config: TagConfig | None = None) -> None:
        self._config = config or TagConfig()
        self._tags: dict[str, ImageTag] = {}
        self._manifests: dict[str, ImageManifest] = {}
        self._log = get_logger("eaip.imgtag.manager")

    @property
    def config(self) -> TagConfig:
        return self._config

    async def create_tag(self, tag: ImageTag) -> ImageTag:
        """Create a new image tag."""
        repo_tags = [t for t in self._tags.values() if t.repository == tag.repository]
        if len(repo_tags) >= self._config.max_tags_per_repository:
            raise TagManagerError(
                f"Maximum tags per repository reached: {self._config.max_tags_per_repository}"
            )
        self._tags[tag.id] = tag
        TagCreated(
            tag_id=tag.id,
            name=tag.name,
            repository=tag.repository,
            digest=tag.digest,
        )
        self._log.info(
            "imgtag.tag.created", tag_id=tag.id, name=tag.name, repository=tag.repository
        )
        return tag

    async def get_tag(self, tag_id: str) -> ImageTag:
        """Get an image tag by ID."""
        tag = self._tags.get(tag_id)
        if tag is None:
            raise TagNotFoundError(f"Image tag not found: {tag_id}")
        return tag

    async def list_tags(self, repository: str | None = None) -> list[ImageTag]:
        """List image tags, optionally filtered by repository."""
        result = list(self._tags.values())
        if repository is not None:
            result = [t for t in result if t.repository == repository]
        return sorted(result, key=lambda t: t.name)

    async def update_tag(self, tag_id: str, digest: str) -> ImageTag:
        """Update the digest of an existing image tag."""
        tag = await self.get_tag(tag_id)
        previous_digest = tag.digest
        updated = tag.model_copy(update={"digest": digest, "updated_at": utc_now()})
        self._tags[tag_id] = updated
        TagUpdated(
            tag_id=tag_id,
            name=tag.name,
            repository=tag.repository,
            previous_digest=previous_digest,
            new_digest=digest,
        )
        self._log.info("imgtag.tag.updated", tag_id=tag_id, previous=previous_digest, new=digest)
        return updated

    async def delete_tag(self, tag_id: str) -> None:
        """Delete an image tag."""
        tag = await self.get_tag(tag_id)
        del self._tags[tag_id]
        TagDeleted(
            tag_id=tag_id,
            name=tag.name,
            repository=tag.repository,
        )
        self._log.info("imgtag.tag.deleted", tag_id=tag_id, name=tag.name)

    async def push_manifest(self, manifest: ImageManifest) -> ImageManifest:
        """Register a new image manifest."""
        self._manifests[manifest.id] = manifest
        ManifestPushed(
            manifest_id=manifest.id,
            repository=manifest.repository,
            digest=manifest.digest,
            size_bytes=manifest.size_bytes,
            tags=manifest.tags,
        )
        self._log.info(
            "imgtag.manifest.pushed",
            manifest_id=manifest.id,
            digest=manifest.digest,
            repository=manifest.repository,
        )
        return manifest

    async def get_manifest(self, manifest_id: str) -> ImageManifest:
        """Get an image manifest by ID."""
        manifest = self._manifests.get(manifest_id)
        if manifest is None:
            raise TagNotFoundError(f"Image manifest not found: {manifest_id}")
        return manifest

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics."""
        return {
            "total_tags": len(self._tags),
            "total_manifests": len(self._manifests),
            "repositories": len({t.repository for t in self._tags.values()}),
        }


__all__ = ["ImageTagManager"]
