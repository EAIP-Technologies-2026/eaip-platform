"""EnvironmentVariableManager — manage environment variables and groups."""

from __future__ import annotations

from eaip.envmgr.events import (
    VariableCreated,
    VariableDeleted,
    VariableGroupCreated,
    VariableUpdated,
)
from eaip.envmgr.exceptions import VariableNotFoundError
from eaip.envmgr.models import (
    EnvironmentVariable,
    EnvMgrConfig,
    VariableGroup,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class EnvironmentVariableManager:
    """Central service for managing environment variables and groups."""

    def __init__(self, config: EnvMgrConfig | None = None) -> None:
        self._config = config or EnvMgrConfig()
        self._variables: dict[str, EnvironmentVariable] = {}
        self._groups: dict[str, VariableGroup] = {}
        self._log = get_logger("eaip.envmgr.service")

    @property
    def config(self) -> EnvMgrConfig:
        return self._config

    async def create_variable(self, variable: EnvironmentVariable) -> EnvironmentVariable:
        """Create a new environment variable."""
        self._variables[variable.id] = variable
        VariableCreated(
            variable_id=variable.id,
            name=variable.name,
            environment=variable.environment,
            scope=variable.scope,
            is_secret=variable.is_secret,
        )
        self._log.info(
            "envmgr.variable.created",
            variable_id=variable.id,
            name=variable.name,
            environment=variable.environment,
        )
        return variable

    async def get_variable(self, variable_id: str) -> EnvironmentVariable:
        """Get an environment variable by ID."""
        variable = self._variables.get(variable_id)
        if variable is None:
            raise VariableNotFoundError(f"Environment variable not found: {variable_id}")
        return variable

    async def update_variable(self, variable_id: str, **updates: object) -> EnvironmentVariable:
        """Update an existing environment variable."""
        variable = self._variables.get(variable_id)
        if variable is None:
            raise VariableNotFoundError(f"Environment variable not found: {variable_id}")
        safe_updates = {
            k: v
            for k, v in updates.items()
            if k in {"value", "description", "is_secret", "scope", "environment"}
        }
        updated = variable.model_copy(
            update={**safe_updates, "version": variable.version + 1, "updated_at": utc_now()}
        )
        self._variables[variable_id] = updated
        VariableUpdated(
            variable_id=variable_id,
            name=updated.name,
            environment=updated.environment,
            version=updated.version,
        )
        self._log.info(
            "envmgr.variable.updated",
            variable_id=variable_id,
            version=updated.version,
        )
        return updated

    async def delete_variable(self, variable_id: str) -> None:
        """Delete an environment variable."""
        variable = self._variables.get(variable_id)
        if variable is None:
            raise VariableNotFoundError(f"Environment variable not found: {variable_id}")
        del self._variables[variable_id]
        VariableDeleted(
            variable_id=variable_id, name=variable.name, environment=variable.environment
        )
        self._log.info("envmgr.variable.deleted", variable_id=variable_id)

    async def list_variables(self, environment: str | None = None) -> list[EnvironmentVariable]:
        """List environment variables, optionally filtered by environment."""
        variables = list(self._variables.values())
        if environment is not None:
            variables = [v for v in variables if v.environment == environment]
        return variables

    async def create_group(self, group: VariableGroup) -> VariableGroup:
        """Create a new variable group."""
        self._groups[group.id] = group
        VariableGroupCreated(
            group_id=group.id,
            name=group.name,
            environment=group.environment,
            variable_count=len(group.variables),
        )
        self._log.info(
            "envmgr.group.created",
            group_id=group.id,
            name=group.name,
            environment=group.environment,
        )
        return group

    async def get_group(self, group_id: str) -> VariableGroup:
        """Get a variable group by ID."""
        group = self._groups.get(group_id)
        if group is None:
            raise VariableNotFoundError(f"Variable group not found: {group_id}")
        return group

    async def list_groups(self, environment: str | None = None) -> list[VariableGroup]:
        """List variable groups, optionally filtered by environment."""
        groups = list(self._groups.values())
        if environment is not None:
            groups = [g for g in groups if g.environment == environment]
        return groups

    async def delete_group(self, group_id: str) -> None:
        """Delete a variable group."""
        if group_id not in self._groups:
            raise VariableNotFoundError(f"Variable group not found: {group_id}")
        del self._groups[group_id]
        self._log.info("envmgr.group.deleted", group_id=group_id)

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about variables and groups."""
        total_variables = len(self._variables)
        total_groups = len(self._groups)
        by_environment: dict[str, int] = {}
        for v in self._variables.values():
            by_environment[v.environment] = by_environment.get(v.environment, 0) + 1
        secrets_count = sum(1 for v in self._variables.values() if v.is_secret)
        return {
            "total_variables": total_variables,
            "total_groups": total_groups,
            "by_environment": by_environment,
            "secrets_count": secrets_count,
        }


__all__ = ["EnvironmentVariableManager"]
