"""Environment Variable Manager — EP-0159."""

from __future__ import annotations

from eaip.envmgr.events import (
    VariableCreated,
    VariableDeleted,
    VariableGroupCreated,
    VariableUpdated,
)
from eaip.envmgr.exceptions import (
    EnvMgrError,
    VariableNotFoundError,
)
from eaip.envmgr.health import EnvMgrHealthCheck
from eaip.envmgr.integration import EnvMgrRuntimeModule
from eaip.envmgr.manager import EnvironmentVariableManager
from eaip.envmgr.models import (
    EnvironmentVariable,
    EnvMgrConfig,
    VariableGroup,
)

__all__ = [
    "EnvMgrConfig",
    "EnvMgrError",
    "EnvMgrHealthCheck",
    "EnvMgrRuntimeModule",
    "EnvironmentVariable",
    "EnvironmentVariableManager",
    "VariableCreated",
    "VariableDeleted",
    "VariableGroup",
    "VariableGroupCreated",
    "VariableNotFoundError",
    "VariableUpdated",
]
