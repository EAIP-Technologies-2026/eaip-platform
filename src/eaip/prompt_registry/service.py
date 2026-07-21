"""Prompt Registry service — CRUD, version management, activation, comparison, search."""

from __future__ import annotations

import difflib
import uuid
from datetime import datetime
from typing import Any

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.prompt_registry.events import (
    PromptApproved,
    PromptArchived,
    PromptCreated,
    PromptDeleted,
    PromptPublished,
    PromptRegistered,
    PromptRejected,
    PromptSearched,
    PromptUnregistered,
    PromptUpdated,
    PromptVersionActivated,
    PromptVersionArchived,
    PromptVersionCompared,
    PromptVersionCreated,
    PromptVersionDeactivated,
    PromptVersionRolledBack,
)
from eaip.prompt_registry.exceptions import (
    PromptApprovalError,
    PromptArchivalError,
    PromptNotFoundError,
    PromptPublishError,
    PromptValidationError,
    PromptVersionConflictError,
    PromptVersionNotFoundError,
)
from eaip.prompt_registry.models import (
    PromptApprovalStatus,
    PromptCategory,
    PromptDefinition,
    PromptDiffResult,
    PromptRegistryConfig,
    PromptSearchResult,
    PromptStatus,
    PromptVersion,
    PromptVersionStatus,
)


class PromptRegistryService:
    """Service for prompt CRUD, version management, activation, comparison, and search."""

    def __init__(
        self,
        config: PromptRegistryConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the PromptRegistryService.

        Args:
            config: Optional PromptRegistryConfig instance.
            event_bus: Optional EventBus instance.
        """
        self._config = config or PromptRegistryConfig()
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.prompt_registry.service")
        self._prompts: dict[str, PromptDefinition] = {}
        self._versions: dict[str, dict[str, PromptVersion]] = {}

    @property
    def config(self) -> PromptRegistryConfig:
        """Return the registry configuration."""
        return self._config

    # ------------------------------------------------------------------
    # Prompt CRUD
    # ------------------------------------------------------------------

    async def create_prompt(
        self,
        name: str,
        description: str = "",
        category: PromptCategory = PromptCategory.CUSTOM,
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
        created_by: str = "",
    ) -> PromptDefinition:
        """Create a new prompt definition in the registry."""
        if not name:
            raise PromptValidationError("Prompt name is required")

        prompt_id = str(uuid.uuid4())
        prompt = PromptDefinition(
            prompt_id=prompt_id,
            name=name,
            description=description,
            category=category,
            tags=tags,
            metadata=metadata or {},
            created_by=created_by,
        )
        self._prompts[prompt_id] = prompt
        self._versions[prompt_id] = {}

        await self._event_bus.publish(
            PromptCreated(prompt_id=prompt_id, name=name, category=category.value),
        )
        await self._event_bus.publish(
            PromptRegistered(prompt_id=prompt_id, name=name),
        )

        self._log.info("prompt.created", prompt_id=prompt_id, name=name)
        return prompt

    async def get_prompt(self, prompt_id: str) -> PromptDefinition:
        """Retrieve a prompt definition by its ID."""
        prompt = self._prompts.get(prompt_id)
        if prompt is None:
            raise PromptNotFoundError(
                f"Prompt {prompt_id!r} not found",
                context={"prompt_id": prompt_id},
            )
        return prompt

    async def update_prompt(
        self,
        prompt_id: str,
        name: str | None = None,
        description: str | None = None,
        category: PromptCategory | None = None,
        tags: tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PromptDefinition:
        """Update an existing prompt definition's fields."""
        existing = await self.get_prompt(prompt_id)

        changes: list[str] = []
        new_name = name if name is not None else existing.name
        if name is not None and name != existing.name:
            changes.append("name")
        new_description = description if description is not None else existing.description
        if description is not None and description != existing.description:
            changes.append("description")
        new_category = category if category is not None else existing.category
        if category is not None and category != existing.category:
            changes.append("category")
        new_tags = tags if tags is not None else existing.tags
        if tags is not None and tags != existing.tags:
            changes.append("tags")
        new_metadata = metadata if metadata is not None else existing.metadata
        if metadata is not None and metadata != existing.metadata:
            changes.append("metadata")

        if not changes:
            return existing

        updated = PromptDefinition(
            prompt_id=existing.prompt_id,
            name=new_name,
            description=new_description,
            current_version=existing.current_version,
            category=new_category,
            status=existing.status,
            tags=new_tags,
            metadata=new_metadata,
            created_at=existing.created_at,
            updated_at=datetime.now(),
            created_by=existing.created_by,
        )
        self._prompts[prompt_id] = updated

        await self._event_bus.publish(
            PromptUpdated(prompt_id=prompt_id, changes=tuple(changes)),
        )

        self._log.info("prompt.updated", prompt_id=prompt_id, changes=changes)
        return updated

    async def delete_prompt(self, prompt_id: str) -> None:
        """Delete a prompt definition and all its versions from the registry."""
        if prompt_id not in self._prompts:
            raise PromptNotFoundError(
                f"Prompt {prompt_id!r} not found",
                context={"prompt_id": prompt_id},
            )

        del self._prompts[prompt_id]
        self._versions.pop(prompt_id, None)

        await self._event_bus.publish(PromptDeleted(prompt_id=prompt_id))
        await self._event_bus.publish(PromptUnregistered(prompt_id=prompt_id))

        self._log.info("prompt.deleted", prompt_id=prompt_id)

    async def list_prompts(
        self,
        category: PromptCategory | None = None,
        status: PromptStatus | None = None,
    ) -> list[PromptDefinition]:
        """List prompt definitions, optionally filtered by category or status."""
        result = list(self._prompts.values())
        if category is not None:
            result = [p for p in result if p.category == category]
        if status is not None:
            result = [p for p in result if p.status == status]
        return result

    # ------------------------------------------------------------------
    # Version management
    # ------------------------------------------------------------------

    async def create_version(
        self,
        prompt_id: str,
        version: str,
        content: str,
        change_log: str = "",
        author: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> PromptVersion:
        """Create a new version for an existing prompt."""
        await self.get_prompt(prompt_id)

        if not version:
            raise PromptValidationError("Version string is required")
        if not content:
            raise PromptValidationError("Version content is required")

        prompt_versions = self._versions.setdefault(prompt_id, {})
        if version in prompt_versions:
            raise PromptVersionConflictError(
                f"Version {version!r} already exists for prompt {prompt_id!r}",
                context={"prompt_id": prompt_id, "version": version},
            )

        if len(prompt_versions) >= self._config.max_versions_per_prompt:
            raise PromptValidationError(
                f"Maximum versions ({self._config.max_versions_per_prompt}) "
                f"reached for prompt {prompt_id!r}",
                context={"prompt_id": prompt_id, "limit": self._config.max_versions_per_prompt},
            )

        version_id = str(uuid.uuid4())
        pv = PromptVersion(
            version_id=version_id,
            prompt_id=prompt_id,
            version=version,
            content=content,
            change_log=change_log,
            author=author,
            metadata=metadata or {},
        )
        prompt_versions[version] = pv

        if self._config.auto_versioning:
            prompt_def = await self.get_prompt(prompt_id)
            updated = PromptDefinition(
                prompt_id=prompt_def.prompt_id,
                name=prompt_def.name,
                description=prompt_def.description,
                current_version=version,
                category=prompt_def.category,
                status=PromptStatus.ACTIVE,
                tags=prompt_def.tags,
                metadata=prompt_def.metadata,
                created_at=prompt_def.created_at,
                updated_at=datetime.now(),
                created_by=prompt_def.created_by,
            )
            self._prompts[prompt_id] = updated

        await self._event_bus.publish(
            PromptVersionCreated(prompt_id=prompt_id, version=version, author=author),
        )

        self._log.info("version.created", prompt_id=prompt_id, version=version)
        return pv

    async def get_version(self, prompt_id: str, version: str) -> PromptVersion:
        """Retrieve a specific version of a prompt by version string."""
        await self.get_prompt(prompt_id)
        prompt_versions = self._versions.get(prompt_id, {})
        pv = prompt_versions.get(version)
        if pv is None:
            raise PromptVersionNotFoundError(
                f"Version {version!r} not found for prompt {prompt_id!r}",
                context={"prompt_id": prompt_id, "version": version},
            )
        return pv

    async def list_versions(self, prompt_id: str) -> list[PromptVersion]:
        """List all versions for a given prompt."""
        await self.get_prompt(prompt_id)
        return list(self._versions.get(prompt_id, {}).values())

    async def activate_version(self, prompt_id: str, version: str) -> PromptVersion:
        """Activate a version, deactivating any other active version."""
        pv = await self.get_version(prompt_id, version)
        if pv.status == PromptVersionStatus.ARCHIVED:
            raise PromptPublishError(
                f"Cannot activate archived version {version!r}",
                context={"prompt_id": prompt_id, "version": version},
            )

        prompt_versions = self._versions[prompt_id]
        for v_str, existing in prompt_versions.items():
            if existing.status == PromptVersionStatus.ACTIVE and v_str != version:
                deactivated = PromptVersion(
                    version_id=existing.version_id,
                    prompt_id=existing.prompt_id,
                    version=existing.version,
                    content=existing.content,
                    change_log=existing.change_log,
                    author=existing.author,
                    status=PromptVersionStatus.DEACTIVATED,
                    metadata=existing.metadata,
                    created_at=existing.created_at,
                    updated_at=datetime.now(),
                )
                prompt_versions[v_str] = deactivated
                await self._event_bus.publish(
                    PromptVersionDeactivated(prompt_id=prompt_id, version=v_str),
                )

        activated = PromptVersion(
            version_id=pv.version_id,
            prompt_id=pv.prompt_id,
            version=pv.version,
            content=pv.content,
            change_log=pv.change_log,
            author=pv.author,
            status=PromptVersionStatus.ACTIVE,
            metadata=pv.metadata,
            created_at=pv.created_at,
            updated_at=datetime.now(),
        )
        prompt_versions[version] = activated

        prompt_def = await self.get_prompt(prompt_id)
        updated = PromptDefinition(
            prompt_id=prompt_def.prompt_id,
            name=prompt_def.name,
            description=prompt_def.description,
            current_version=version,
            category=prompt_def.category,
            status=PromptStatus.ACTIVE,
            tags=prompt_def.tags,
            metadata=prompt_def.metadata,
            created_at=prompt_def.created_at,
            updated_at=datetime.now(),
            created_by=prompt_def.created_by,
        )
        self._prompts[prompt_id] = updated

        await self._event_bus.publish(
            PromptVersionActivated(prompt_id=prompt_id, version=version),
        )

        self._log.info("version.activated", prompt_id=prompt_id, version=version)
        return activated

    async def deactivate_version(self, prompt_id: str, version: str) -> PromptVersion:
        """Deactivate a version without archiving it."""
        pv = await self.get_version(prompt_id, version)
        deactivated = PromptVersion(
            version_id=pv.version_id,
            prompt_id=pv.prompt_id,
            version=pv.version,
            content=pv.content,
            change_log=pv.change_log,
            author=pv.author,
            status=PromptVersionStatus.DEACTIVATED,
            metadata=pv.metadata,
            created_at=pv.created_at,
            updated_at=datetime.now(),
        )
        self._versions[prompt_id][version] = deactivated

        await self._event_bus.publish(
            PromptVersionDeactivated(prompt_id=prompt_id, version=version),
        )

        self._log.info("version.deactivated", prompt_id=prompt_id, version=version)
        return deactivated

    async def archive_version(self, prompt_id: str, version: str) -> PromptVersion:
        """Archive a specific version, preventing further activation."""
        pv = await self.get_version(prompt_id, version)
        archived = PromptVersion(
            version_id=pv.version_id,
            prompt_id=pv.prompt_id,
            version=pv.version,
            content=pv.content,
            change_log=pv.change_log,
            author=pv.author,
            status=PromptVersionStatus.ARCHIVED,
            metadata=pv.metadata,
            created_at=pv.created_at,
            updated_at=datetime.now(),
        )
        self._versions[prompt_id][version] = archived

        await self._event_bus.publish(
            PromptVersionArchived(prompt_id=prompt_id, version=version),
        )

        self._log.info("version.archived", prompt_id=prompt_id, version=version)
        return archived

    async def rollback_version(
        self,
        prompt_id: str,
        target_version: str,
    ) -> PromptVersion:
        """Roll back the prompt to a previous version and activate it."""
        pv = await self.get_version(prompt_id, target_version)

        existing = await self.get_prompt(prompt_id)
        previous_version = existing.current_version

        updated = PromptDefinition(
            prompt_id=existing.prompt_id,
            name=existing.name,
            description=existing.description,
            current_version=target_version,
            category=existing.category,
            status=PromptStatus.ACTIVE,
            tags=existing.tags,
            metadata=existing.metadata,
            created_at=existing.created_at,
            updated_at=datetime.now(),
            created_by=existing.created_by,
        )
        self._prompts[prompt_id] = updated

        activated = PromptVersion(
            version_id=pv.version_id,
            prompt_id=pv.prompt_id,
            version=pv.version,
            content=pv.content,
            change_log=pv.change_log,
            author=pv.author,
            status=PromptVersionStatus.ACTIVE,
            metadata=pv.metadata,
            created_at=pv.created_at,
            updated_at=datetime.now(),
        )
        self._versions[prompt_id][target_version] = activated

        await self._event_bus.publish(
            PromptVersionRolledBack(
                prompt_id=prompt_id,
                target_version=target_version,
                previous_version=previous_version,
            ),
        )

        self._log.info(
            "version.rolled_back",
            prompt_id=prompt_id,
            target=target_version,
            previous=previous_version,
        )
        return activated

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    async def compare_versions(
        self,
        prompt_id: str,
        version_a: str,
        version_b: str,
    ) -> PromptDiffResult:
        """Compare two versions and return a diff result."""
        pv_a = await self.get_version(prompt_id, version_a)
        pv_b = await self.get_version(prompt_id, version_b)

        lines_a = pv_a.content.splitlines(keepends=True)
        lines_b = pv_b.content.splitlines(keepends=True)

        differ = difflib.Differ()
        diff = list(differ.compare(lines_a, lines_b))

        additions: list[str] = []
        removals: list[str] = []
        modifications: list[str] = []

        for line in diff:
            if line.startswith("+ ") and not line.startswith("+ +"):
                additions.append(line[2:].rstrip())
            elif line.startswith("- ") and not line.startswith("- -"):
                removals.append(line[2:].rstrip())
            elif line.startswith("? "):
                modifications.append(line[2:].rstrip())

        summary_parts: list[str] = []
        if additions:
            summary_parts.append(f"+{len(additions)} additions")
        if removals:
            summary_parts.append(f"-{len(removals)} removals")
        summary = ", ".join(summary_parts) if summary_parts else "no changes"

        result = PromptDiffResult(
            version_a=version_a,
            version_b=version_b,
            additions=tuple(additions),
            removals=tuple(removals),
            modifications=tuple(modifications),
            summary=summary,
        )

        await self._event_bus.publish(
            PromptVersionCompared(
                prompt_id=prompt_id,
                version_a=version_a,
                version_b=version_b,
            ),
        )

        self._log.info(
            "version.compared",
            prompt_id=prompt_id,
            v_a=version_a,
            v_b=version_b,
        )
        return result

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_prompts(
        self,
        query: str = "",
        category: PromptCategory | None = None,
        status: PromptStatus | None = None,
        tags: tuple[str, ...] = (),
        page: int = 1,
        page_size: int = 20,
    ) -> PromptSearchResult:
        """Search prompts by name, description, category, status, or tags."""
        results = list(self._prompts.values())

        if query:
            q = query.lower()
            results = [p for p in results if q in p.name.lower() or q in p.description.lower()]

        if category is not None:
            results = [p for p in results if p.category == category]

        if status is not None:
            results = [p for p in results if p.status == status]

        if tags:
            results = [p for p in results if any(t in p.tags for t in tags)]

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        paged = tuple(results[start:end])

        await self._event_bus.publish(
            PromptSearched(query=query, total_results=total),
        )

        return PromptSearchResult(
            total=total,
            results=paged,
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # Lifecycle actions
    # ------------------------------------------------------------------

    async def publish_prompt(self, prompt_id: str, version: str) -> PromptDefinition:
        """Publish a prompt by setting it to active status with the given version."""
        await self.get_version(prompt_id, version)
        existing = await self.get_prompt(prompt_id)
        updated = PromptDefinition(
            prompt_id=existing.prompt_id,
            name=existing.name,
            description=existing.description,
            current_version=version,
            category=existing.category,
            status=PromptStatus.ACTIVE,
            tags=existing.tags,
            metadata=existing.metadata,
            created_at=existing.created_at,
            updated_at=datetime.now(),
            created_by=existing.created_by,
        )
        self._prompts[prompt_id] = updated

        await self._event_bus.publish(
            PromptPublished(prompt_id=prompt_id, version=version),
        )

        self._log.info("prompt.published", prompt_id=prompt_id, version=version)
        return updated

    async def archive_prompt(self, prompt_id: str) -> PromptDefinition:
        """Archive a prompt and all its non-archived versions."""
        existing = await self.get_prompt(prompt_id)
        if existing.status == PromptStatus.ARCHIVED:
            raise PromptArchivalError(
                f"Prompt {prompt_id!r} is already archived",
                context={"prompt_id": prompt_id},
            )

        updated = PromptDefinition(
            prompt_id=existing.prompt_id,
            name=existing.name,
            description=existing.description,
            current_version=existing.current_version,
            category=existing.category,
            status=PromptStatus.ARCHIVED,
            tags=existing.tags,
            metadata=existing.metadata,
            created_at=existing.created_at,
            updated_at=datetime.now(),
            created_by=existing.created_by,
        )
        self._prompts[prompt_id] = updated

        prompt_versions = self._versions.get(prompt_id, {})
        for v_str, pv in prompt_versions.items():
            if pv.status not in (PromptVersionStatus.ARCHIVED,):
                archived = PromptVersion(
                    version_id=pv.version_id,
                    prompt_id=pv.prompt_id,
                    version=pv.version,
                    content=pv.content,
                    change_log=pv.change_log,
                    author=pv.author,
                    status=PromptVersionStatus.ARCHIVED,
                    metadata=pv.metadata,
                    created_at=pv.created_at,
                    updated_at=datetime.now(),
                )
                prompt_versions[v_str] = archived

        await self._event_bus.publish(PromptArchived(prompt_id=prompt_id))

        self._log.info("prompt.archived", prompt_id=prompt_id)
        return updated

    async def approve_prompt(
        self,
        prompt_id: str,
        version: str,
        reviewer: str = "",
    ) -> PromptDefinition:
        """Approve a prompt version and set it as the active version."""
        pv = await self.get_version(prompt_id, version)

        approved_v = PromptVersion(
            version_id=pv.version_id,
            prompt_id=pv.prompt_id,
            version=pv.version,
            content=pv.content,
            change_log=pv.change_log,
            author=pv.author,
            status=PromptVersionStatus.ACTIVE,
            metadata={**pv.metadata, "approval_status": PromptApprovalStatus.APPROVED.value},
            created_at=pv.created_at,
            updated_at=datetime.now(),
        )
        self._versions[prompt_id][version] = approved_v

        prompt_def = await self.get_prompt(prompt_id)
        updated = PromptDefinition(
            prompt_id=prompt_def.prompt_id,
            name=prompt_def.name,
            description=prompt_def.description,
            current_version=version,
            category=prompt_def.category,
            status=PromptStatus.ACTIVE,
            tags=prompt_def.tags,
            metadata=prompt_def.metadata,
            created_at=prompt_def.created_at,
            updated_at=datetime.now(),
            created_by=prompt_def.created_by,
        )
        self._prompts[prompt_id] = updated

        await self._event_bus.publish(
            PromptApproved(prompt_id=prompt_id, version=version, reviewer=reviewer),
        )

        self._log.info("prompt.approved", prompt_id=prompt_id, version=version)
        return updated

    async def reject_prompt(
        self,
        prompt_id: str,
        version: str,
        reviewer: str = "",
        reason: str = "",
    ) -> PromptVersion:
        """Reject a prompt version with a reason."""
        pv = await self.get_version(prompt_id, version)

        if not reason:
            raise PromptApprovalError("Rejection reason is required")

        rejected_v = PromptVersion(
            version_id=pv.version_id,
            prompt_id=pv.prompt_id,
            version=pv.version,
            content=pv.content,
            change_log=pv.change_log,
            author=pv.author,
            status=pv.status,
            metadata={**pv.metadata, "approval_status": PromptApprovalStatus.REJECTED.value},
            created_at=pv.created_at,
            updated_at=datetime.now(),
        )
        self._versions[prompt_id][version] = rejected_v

        await self._event_bus.publish(
            PromptRejected(
                prompt_id=prompt_id,
                version=version,
                reviewer=reviewer,
                reason=reason,
            ),
        )

        self._log.info("prompt.rejected", prompt_id=prompt_id, version=version)
        return rejected_v


__all__ = ["PromptRegistryService"]
