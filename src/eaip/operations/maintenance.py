"""Maintenance window management."""

from __future__ import annotations

from datetime import UTC, datetime

from eaip.logging.context import get_logger
from eaip.operations.exceptions import MaintenanceActiveError
from eaip.operations.models import MaintenanceWindow


class MaintenanceManager:
    """Manages maintenance windows and component maintenance mode."""

    def __init__(self) -> None:
        """Initialize the maintenance manager."""
        self._windows: dict[str, MaintenanceWindow] = {}
        self._maintenance_components: dict[str, str] = {}
        self._log = get_logger("eaip.operations.maintenance")

    async def schedule_window(self, window: MaintenanceWindow) -> MaintenanceWindow:
        """Schedule a new maintenance window.

        Args:
            window: The maintenance window to schedule.

        Returns:
            The scheduled maintenance window.

        Raises:
            MaintenanceActiveError: If an overlapping active window exists.
        """
        for existing in self._windows.values():
            if existing.status == "active" and (
                window.scheduled_start < existing.scheduled_end
                and window.scheduled_end > existing.scheduled_start
            ):
                raise MaintenanceActiveError(
                    "Overlapping active maintenance window exists",
                    context={"existing_id": existing.id, "existing_name": existing.name},
                )
        self._windows[window.id] = window
        self._log.info("maintenance.window.scheduled", window_id=window.id, name=window.name)
        return window

    async def start_window(self, window_id: str) -> MaintenanceWindow:
        """Start a scheduled maintenance window.

        Args:
            window_id: The ID of the window to start.

        Returns:
            The started maintenance window.

        Raises:
            MaintenanceActiveError: If the window is not found or cannot be started.
        """
        window = self._windows.get(window_id)
        if window is None:
            raise MaintenanceActiveError(
                "Maintenance window not found",
                context={"window_id": window_id},
            )
        if window.status != "scheduled":
            raise MaintenanceActiveError(
                f"Cannot start window with status {window.status}",
                context={"window_id": window_id, "status": window.status},
            )
        started = MaintenanceWindow(
            id=window.id,
            name=window.name,
            description=window.description,
            status="active",
            scheduled_start=window.scheduled_start,
            scheduled_end=window.scheduled_end,
            actual_start=datetime.now(UTC),
            actual_end=window.actual_end,
            components=window.components,
            reason=window.reason,
            created_by=window.created_by,
            metadata=window.metadata,
            notify_users=window.notify_users,
        )
        self._windows[window_id] = started
        for comp in started.components:
            self._maintenance_components[comp] = window_id
        self._log.info("maintenance.window.started", window_id=window_id)
        return started

    async def complete_window(self, window_id: str) -> MaintenanceWindow:
        """Complete an active maintenance window.

        Args:
            window_id: The ID of the window to complete.

        Returns:
            The completed maintenance window.

        Raises:
            MaintenanceActiveError: If the window is not found or not active.
        """
        window = self._windows.get(window_id)
        if window is None:
            raise MaintenanceActiveError(
                "Maintenance window not found",
                context={"window_id": window_id},
            )
        if window.status != "active":
            raise MaintenanceActiveError(
                f"Cannot complete window with status {window.status}",
                context={"window_id": window_id, "status": window.status},
            )
        completed = MaintenanceWindow(
            id=window.id,
            name=window.name,
            description=window.description,
            status="completed",
            scheduled_start=window.scheduled_start,
            scheduled_end=window.scheduled_end,
            actual_start=window.actual_start,
            actual_end=datetime.now(UTC),
            components=window.components,
            reason=window.reason,
            created_by=window.created_by,
            metadata=window.metadata,
            notify_users=window.notify_users,
        )
        self._windows[window_id] = completed
        for comp in completed.components:
            self._maintenance_components.pop(comp, None)
        self._log.info("maintenance.window.completed", window_id=window_id)
        return completed

    async def cancel_window(self, window_id: str) -> MaintenanceWindow:
        """Cancel a scheduled or active maintenance window.

        Args:
            window_id: The ID of the window to cancel.

        Returns:
            The cancelled maintenance window.

        Raises:
            MaintenanceActiveError: If the window is not found or cannot be cancelled.
        """
        window = self._windows.get(window_id)
        if window is None:
            raise MaintenanceActiveError(
                "Maintenance window not found",
                context={"window_id": window_id},
            )
        if window.status not in ("scheduled", "active"):
            raise MaintenanceActiveError(
                f"Cannot cancel window with status {window.status}",
                context={"window_id": window_id, "status": window.status},
            )
        cancelled = MaintenanceWindow(
            id=window.id,
            name=window.name,
            description=window.description,
            status="cancelled",
            scheduled_start=window.scheduled_start,
            scheduled_end=window.scheduled_end,
            actual_start=window.actual_start,
            actual_end=datetime.now(UTC),
            components=window.components,
            reason=window.reason,
            created_by=window.created_by,
            metadata=window.metadata,
            notify_users=window.notify_users,
        )
        self._windows[window_id] = cancelled
        for comp in cancelled.components:
            self._maintenance_components.pop(comp, None)
        self._log.info("maintenance.window.cancelled", window_id=window_id)
        return cancelled

    async def get_window(self, window_id: str) -> MaintenanceWindow | None:
        """Get a maintenance window by ID.

        Args:
            window_id: The window identifier.

        Returns:
            The maintenance window, or None if not found.
        """
        return self._windows.get(window_id)

    async def list_windows(self, status: str | None = None) -> list[MaintenanceWindow]:
        """List maintenance windows, optionally filtered by status.

        Args:
            status: Optional status filter.

        Returns:
            A list of matching maintenance windows.
        """
        if status is None:
            return list(self._windows.values())
        return [w for w in self._windows.values() if w.status == status]

    async def is_in_maintenance(self, component: str) -> bool:
        """Check if a component is currently in maintenance mode.

        Args:
            component: The component name to check.

        Returns:
            True if the component is in maintenance, False otherwise.
        """
        return component in self._maintenance_components

    async def enter_maintenance_mode(self, component: str, reason: str) -> bool:
        """Manually place a component into maintenance mode.

        Args:
            component: The component name.
            reason: The reason for entering maintenance.

        Returns:
            True if the component was placed into maintenance.

        Raises:
            MaintenanceActiveError: If the component is already in maintenance.
        """
        if component in self._maintenance_components:
            raise MaintenanceActiveError(
                f"Component {component} is already in maintenance",
                context={"component": component},
            )
        self._maintenance_components[component] = f"manual:{reason}"
        self._log.info("maintenance.entered", component=component, reason=reason)
        return True

    async def exit_maintenance_mode(self, component: str) -> bool:
        """Remove a component from maintenance mode.

        Args:
            component: The component name.

        Returns:
            True if the component was removed from maintenance.

        Raises:
            MaintenanceActiveError: If the component is not in maintenance.
        """
        if component not in self._maintenance_components:
            raise MaintenanceActiveError(
                f"Component {component} is not in maintenance",
                context={"component": component},
            )
        self._maintenance_components.pop(component)
        self._log.info("maintenance.exited", component=component)
        return True

    @property
    def active_components(self) -> dict[str, str]:
        """Return a copy of the currently maintenance-locked components."""
        return dict(self._maintenance_components)


__all__ = ["MaintenanceManager"]
