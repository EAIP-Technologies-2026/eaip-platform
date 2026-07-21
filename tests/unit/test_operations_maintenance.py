"""Tests for :mod:`eaip.operations.maintenance`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.operations.exceptions import MaintenanceActiveError
from eaip.operations.maintenance import MaintenanceManager
from eaip.operations.models import MaintenanceWindow


@pytest.fixture
def manager() -> MaintenanceManager:
    return MaintenanceManager()


@pytest.fixture
def future_window() -> MaintenanceWindow:
    now = datetime.now(UTC)
    return MaintenanceWindow(
        id="mw-1",
        name="Scheduled upgrade",
        scheduled_start=now + timedelta(hours=1),
        scheduled_end=now + timedelta(hours=3),
    )


class TestMaintenanceManager:
    async def test_schedule_window(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        result = await manager.schedule_window(future_window)
        assert result.id == "mw-1"
        assert result.status == "scheduled"

    async def test_schedule_window_duplicate(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        with pytest.raises(MaintenanceActiveError):
            await manager.start_window("mw-nonexistent")

    async def test_get_window(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        result = await manager.get_window("mw-1")
        assert result is not None
        assert result.name == "Scheduled upgrade"

    async def test_get_window_not_found(self, manager: MaintenanceManager) -> None:
        result = await manager.get_window("does-not-exist")
        assert result is None

    async def test_list_windows_all(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        windows = await manager.list_windows()
        assert len(windows) == 1

    async def test_list_windows_by_status(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        scheduled = await manager.list_windows(status="scheduled")
        assert len(scheduled) == 1
        active = await manager.list_windows(status="active")
        assert len(active) == 0

    async def test_start_window(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        started = await manager.start_window("mw-1")
        assert started.status == "active"
        assert started.actual_start is not None

    async def test_start_window_not_found(self, manager: MaintenanceManager) -> None:
        with pytest.raises(MaintenanceActiveError):
            await manager.start_window("does-not-exist")

    async def test_start_window_wrong_status(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        await manager.start_window("mw-1")
        with pytest.raises(MaintenanceActiveError, match="Cannot start window with status"):
            await manager.start_window("mw-1")

    async def test_complete_window(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        await manager.start_window("mw-1")
        completed = await manager.complete_window("mw-1")
        assert completed.status == "completed"
        assert completed.actual_end is not None

    async def test_complete_window_not_found(self, manager: MaintenanceManager) -> None:
        with pytest.raises(MaintenanceActiveError):
            await manager.complete_window("does-not-exist")

    async def test_complete_window_not_active(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        with pytest.raises(MaintenanceActiveError, match="Cannot complete window with status"):
            await manager.complete_window("mw-1")

    async def test_cancel_window(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        cancelled = await manager.cancel_window("mw-1")
        assert cancelled.status == "cancelled"

    async def test_cancel_window_not_found(self, manager: MaintenanceManager) -> None:
        with pytest.raises(MaintenanceActiveError):
            await manager.cancel_window("does-not-exist")

    async def test_cancel_window_wrong_status(
        self, manager: MaintenanceManager, future_window: MaintenanceWindow
    ) -> None:
        await manager.schedule_window(future_window)
        await manager.cancel_window("mw-1")
        with pytest.raises(MaintenanceActiveError, match="Cannot cancel window with status"):
            await manager.cancel_window("mw-1")

    async def test_is_in_maintenance(self, manager: MaintenanceManager) -> None:
        await manager.enter_maintenance_mode("db", "testing")
        assert await manager.is_in_maintenance("db") is True

    async def test_is_in_maintenance_false(self, manager: MaintenanceManager) -> None:
        assert await manager.is_in_maintenance("nonexistent") is False

    async def test_enter_maintenance_mode(self, manager: MaintenanceManager) -> None:
        result = await manager.enter_maintenance_mode("db", "emergency fix")
        assert result is True
        assert await manager.is_in_maintenance("db") is True

    async def test_enter_maintenance_mode_already_active(self, manager: MaintenanceManager) -> None:
        await manager.enter_maintenance_mode("db", "reason")
        with pytest.raises(MaintenanceActiveError, match="already in maintenance"):
            await manager.enter_maintenance_mode("db", "another reason")

    async def test_exit_maintenance_mode(self, manager: MaintenanceManager) -> None:
        await manager.enter_maintenance_mode("cache", "testing")
        result = await manager.exit_maintenance_mode("cache")
        assert result is True
        assert await manager.is_in_maintenance("cache") is False

    async def test_exit_maintenance_mode_not_active(self, manager: MaintenanceManager) -> None:
        with pytest.raises(MaintenanceActiveError, match="not in maintenance"):
            await manager.exit_maintenance_mode("cache")

    async def test_active_components_property(self, manager: MaintenanceManager) -> None:
        await manager.enter_maintenance_mode("db", "fix")
        await manager.enter_maintenance_mode("cache", "upgrade")
        assert "db" in manager.active_components
        assert "cache" in manager.active_components
        assert len(manager.active_components) == 2
