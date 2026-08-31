"""Blue-Green Deployment Manager — manage zero-downtime deployments with blue-green strategy."""

from __future__ import annotations

from eaip.bluegreen.events import (
    HealthCheckFailed,
    SwitchCompleted,
    SwitchRolledBack,
    SwitchStarted,
)
from eaip.bluegreen.exceptions import (
    BlueGreenError,
    SwitchError,
)
from eaip.bluegreen.health import BlueGreenHealthCheck
from eaip.bluegreen.integration import BlueGreenRuntimeModule
from eaip.bluegreen.manager import BlueGreenManager
from eaip.bluegreen.models import (
    BlueGreenConfig,
    DeploymentSwitch,
    Environment,
    EnvironmentStatus,
    EnvironmentType,
    SwitchStrategy,
)

__all__ = [
    "BlueGreenConfig",
    "BlueGreenError",
    "BlueGreenHealthCheck",
    "BlueGreenManager",
    "BlueGreenRuntimeModule",
    "DeploymentSwitch",
    "Environment",
    "EnvironmentStatus",
    "EnvironmentType",
    "HealthCheckFailed",
    "SwitchCompleted",
    "SwitchError",
    "SwitchRolledBack",
    "SwitchStarted",
    "SwitchStrategy",
]
