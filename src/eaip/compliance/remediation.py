"""Remediation tracking for compliance findings."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.compliance.events import RemediationCreated, RemediationResolved
from eaip.compliance.exceptions import ComplianceError
from eaip.compliance.models import RemediationItem
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class RemediationTracker:
    """Tracks remediation items for non-compliant controls."""

    def __init__(self) -> None:
        """Initialize the remediation tracker."""
        self._log = get_logger("eaip.compliance.remediation")
        self._items: dict[str, RemediationItem] = {}

    async def create_item(
        self,
        control_id: str,
        description: str,
        assigned_to: str | None = None,
        event_bus: Any = None,
    ) -> RemediationItem:
        """Create a remediation item for a control."""
        item = RemediationItem(
            item_id=str(uuid.uuid4()),
            control_id=control_id,
            description=description,
            status="open",
            created_at=utc_now(),
            assigned_to=assigned_to,
        )
        self._items[item.item_id] = item
        self._log.info("remediation.created", item_id=item.item_id, control_id=control_id)

        if event_bus is not None:
            await event_bus.publish(
                RemediationCreated(
                    item_id=item.item_id,
                    control_id=control_id,
                    description=description,
                )
            )

        return item

    async def resolve_item(
        self,
        item_id: str,
        event_bus: Any = None,
    ) -> RemediationItem:
        """Resolve a remediation item."""
        item = self._items.get(item_id)
        if item is None:
            raise ComplianceError(f"Remediation item {item_id!r} not found")

        resolved = RemediationItem(
            item_id=item.item_id,
            control_id=item.control_id,
            description=item.description,
            status="resolved",
            created_at=item.created_at,
            resolved_at=utc_now(),
            assigned_to=item.assigned_to,
        )
        self._items[item_id] = resolved
        self._log.info("remediation.resolved", item_id=item_id)

        if event_bus is not None:
            await event_bus.publish(
                RemediationResolved(
                    item_id=item_id,
                    control_id=item.control_id,
                )
            )

        return resolved

    def get_item(self, item_id: str) -> RemediationItem | None:
        """Get a remediation item by ID."""
        return self._items.get(item_id)

    def list_items(self, status: str | None = None) -> tuple[RemediationItem, ...]:
        """List remediation items, optionally filtered by status."""
        items = list(self._items.values())
        if status is not None:
            items = [i for i in items if i.status == status]
        return tuple(items)

    def count_by_status(self) -> dict[str, int]:
        """Count remediation items by status."""
        counts: dict[str, int] = {}
        for item in self._items.values():
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts

    def clear(self) -> None:
        """Clear all remediation items."""
        self._items.clear()


__all__ = ["RemediationTracker"]
