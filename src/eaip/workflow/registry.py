"""Workflow registry — lifecycle management for workflow definitions.

Supports CRUD, versioning, archiving, labels, tags, ownership, and
event publishing for every lifecycle state change.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.workflow.events import (
    WorkflowArchived,
    WorkflowCreated,
    WorkflowUpdated,
)
from eaip.workflow.exceptions import WorkflowNotFoundError
from eaip.workflow.models import WorkflowDefinition, WorkflowStatus


class WorkflowRegistry:
    """In-memory registry for workflow definitions with lifecycle management.

    Supports CRUD, versioning, archiving, and metadata (labels, tags, ownership).
    """

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}
        self._statuses: dict[str, WorkflowStatus] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.workflow.registry")

    # ── CRUD ────────────────────────────────────────────────────────

    async def create(
        self, definition: WorkflowDefinition, metadata: dict[str, Any] | None = None
    ) -> WorkflowDefinition:
        """Register a new workflow definition.

        Args:
            definition: The workflow definition.
            metadata: Optional metadata (labels, tags, ownership).

        Returns:
            The registered definition.
        """
        self._definitions[definition.id] = definition
        self._statuses[definition.id] = WorkflowStatus.PENDING
        if metadata:
            self._metadata[definition.id] = metadata
        await self._publish(
            WorkflowCreated(
                workflow_id=definition.id,
                name=definition.name,
                version=definition.version,
            )
        )
        self._log.info("workflow.created", workflow_id=definition.id, name=definition.name)
        return definition

    async def update(self, workflow_id: str, **updates: Any) -> WorkflowDefinition:
        """Update an existing workflow definition.

        Args:
            workflow_id: The workflow identifier.
            **updates: Fields to update.

        Returns:
            The updated definition.

        Raises:
            WorkflowNotFoundError: If the definition does not exist.
        """
        definition = self._definitions.get(workflow_id)
        if definition is None:
            raise WorkflowNotFoundError(f"Workflow {workflow_id!r} not found")
        updated = definition.model_copy(update=updates)
        self._definitions[workflow_id] = updated
        await self._publish(
            WorkflowUpdated(
                workflow_id=workflow_id,
                name=updated.name,
                changes=tuple(updates.keys()),
            )
        )
        self._log.info("workflow.updated", workflow_id=workflow_id)
        return updated

    async def get(self, workflow_id: str) -> WorkflowDefinition | None:
        """Retrieve a workflow definition by ID."""
        return self._definitions.get(workflow_id)

    async def delete(self, workflow_id: str) -> None:
        """Delete a workflow definition.

        Raises:
            WorkflowNotFoundError: If the definition does not exist.
        """
        definition = self._definitions.pop(workflow_id, None)
        if definition is None:
            raise WorkflowNotFoundError(f"Workflow {workflow_id!r} not found")
        self._statuses.pop(workflow_id, None)
        self._metadata.pop(workflow_id, None)
        self._log.info("workflow.deleted", workflow_id=workflow_id)

    async def list_definitions(
        self,
        status: WorkflowStatus | None = None,
        tag: str | None = None,
    ) -> Sequence[WorkflowDefinition]:
        """List workflow definitions, optionally filtered."""
        results = list(self._definitions.values())
        if status is not None:
            results = [d for d in results if self._statuses.get(d.id) == status]
        if tag is not None:
            results = [d for d in results if tag in self._metadata.get(d.id, {}).get("tags", [])]
        return results

    async def archive(self, workflow_id: str) -> WorkflowDefinition:
        """Archive a workflow definition.

        Raises:
            WorkflowNotFoundError: If the definition does not exist.
        """
        definition = self._definitions.get(workflow_id)
        if definition is None:
            raise WorkflowNotFoundError(f"Workflow {workflow_id!r} not found")
        self._statuses[workflow_id] = WorkflowStatus.ARCHIVED
        await self._publish(WorkflowArchived(workflow_id=workflow_id, name=definition.name))
        self._log.info("workflow.archived", workflow_id=workflow_id)
        return definition

    async def get_status(self, workflow_id: str) -> WorkflowStatus | None:
        """Get the current lifecycle status."""
        return self._statuses.get(workflow_id)

    async def set_metadata(self, workflow_id: str, metadata: dict[str, Any]) -> None:
        """Set metadata (labels, tags, ownership) for a definition."""
        self._metadata[workflow_id] = metadata

    async def get_metadata(self, workflow_id: str) -> dict[str, Any]:
        """Get metadata for a definition."""
        return self._metadata.get(workflow_id, {})

    async def duplicate(self, workflow_id: str, new_id: str) -> WorkflowDefinition:
        """Duplicate a workflow definition.

        Args:
            workflow_id: Source workflow ID.
            new_id: ID for the new definition.

        Returns:
            The duplicated definition.
        """
        source = self._definitions.get(workflow_id)
        if source is None:
            raise WorkflowNotFoundError(f"Workflow {workflow_id!r} not found")
        new_def = source.model_copy(update={"id": new_id, "name": f"{source.name} (Copy)"})
        return await self.create(new_def)

    async def _publish(self, event: Any) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)


__all__ = ["WorkflowRegistry"]
