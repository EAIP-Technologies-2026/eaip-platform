"""Custom Dashboard Builder — create, manage, and render custom dashboards."""

from __future__ import annotations

from eaip.dashboard.builder import DashboardBuilder
from eaip.dashboard.events import (
    DashboardCreated,
    DashboardDeleted,
    DashboardUpdated,
    WidgetAdded,
)
from eaip.dashboard.exceptions import (
    DashboardError,
    DashboardNotFoundError,
)
from eaip.dashboard.health import DashboardHealthCheck
from eaip.dashboard.integration import DashboardRuntimeModule
from eaip.dashboard.models import (
    Dashboard,
    DashboardConfig,
    DashboardLayout,
    WidgetDefinition,
    WidgetType,
)

__all__ = [
    "Dashboard",
    "DashboardBuilder",
    "DashboardConfig",
    "DashboardCreated",
    "DashboardDeleted",
    "DashboardError",
    "DashboardHealthCheck",
    "DashboardLayout",
    "DashboardNotFoundError",
    "DashboardRuntimeModule",
    "DashboardUpdated",
    "WidgetAdded",
    "WidgetDefinition",
    "WidgetType",
]
