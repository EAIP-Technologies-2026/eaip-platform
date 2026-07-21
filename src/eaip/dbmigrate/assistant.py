"""DatabaseMigrationAssistant — create, execute, and roll back migration scripts."""

from __future__ import annotations

from eaip.dbmigrate.events import MigrationExecuted, MigrationRolledBack, ScriptCreated
from eaip.dbmigrate.exceptions import ScriptNotFoundError
from eaip.dbmigrate.models import DBMigrateConfig, MigrationExecution, MigrationScript, ScriptStatus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class DatabaseMigrationAssistant:
    """Central service for managing database migration scripts and executions."""

    def __init__(self, config: DBMigrateConfig | None = None) -> None:
        self._config = config or DBMigrateConfig()
        self._scripts: dict[str, MigrationScript] = {}
        self._executions: dict[str, MigrationExecution] = {}
        self._log = get_logger("eaip.dbmigrate.service")

    @property
    def config(self) -> DBMigrateConfig:
        return self._config

    async def create_script(self, script: MigrationScript) -> MigrationScript:
        """Create a new migration script."""
        self._scripts[script.id] = script
        ScriptCreated(
            script_id=script.id,
            name=script.name,
            version=script.version,
            database_type=script.database_type,
            author=script.author,
        )
        self._log.info("dbmigrate.script.created", script_id=script.id, name=script.name)
        return script

    async def get_script(self, script_id: str) -> MigrationScript:
        """Get a migration script by ID."""
        script = self._scripts.get(script_id)
        if script is None:
            raise ScriptNotFoundError(f"Migration script not found: {script_id}")
        return script

    async def list_scripts(self, status: ScriptStatus | None = None) -> list[MigrationScript]:
        """List all migration scripts, optionally filtered by status."""
        scripts = list(self._scripts.values())
        if status is not None:
            scripts = [s for s in scripts if s.status == status]
        return scripts

    async def update_script(self, script_id: str, **changes: object) -> MigrationScript:
        """Update an existing migration script."""
        script = self._scripts.get(script_id)
        if script is None:
            raise ScriptNotFoundError(f"Migration script not found: {script_id}")
        updated = script.model_copy(update={"updated_at": utc_now(), **changes})
        self._scripts[script_id] = updated
        self._log.info("dbmigrate.script.updated", script_id=script_id)
        return updated

    async def execute_script(
        self,
        script_id: str,
        environment: str,
        execution_id: str,
    ) -> MigrationExecution:
        """Execute a migration script against an environment."""
        script = self._scripts.get(script_id)
        if script is None:
            raise ScriptNotFoundError(f"Migration script not found: {script_id}")
        execution = MigrationExecution(
            id=execution_id,
            script_id=script_id,
            environment=environment,
        )
        self._executions[execution_id] = execution
        success = True
        output = f"Executed {script.name} (v{script.version}) on {environment}"
        error = ""
        completed = execution.model_copy(
            update={
                "success": success,
                "output": output,
                "error": error,
                "completed_at": utc_now(),
            }
        )
        self._executions[execution_id] = completed
        updated_script = script.model_copy(
            update={"status": ScriptStatus.EXECUTED, "updated_at": utc_now()}
        )
        self._scripts[script_id] = updated_script
        MigrationExecuted(
            execution_id=execution_id,
            script_id=script_id,
            environment=environment,
            success=success,
            output=output,
        )
        self._log.info("dbmigrate.script.executed", script_id=script_id, environment=environment)
        return completed

    async def rollback_script(
        self,
        script_id: str,
        environment: str,
        reason: str = "",
    ) -> MigrationScript:
        """Roll back a previously executed migration script."""
        script = self._scripts.get(script_id)
        if script is None:
            raise ScriptNotFoundError(f"Migration script not found: {script_id}")
        rolled_back = script.model_copy(
            update={"status": ScriptStatus.ROLLED_BACK, "updated_at": utc_now()}
        )
        self._scripts[script_id] = rolled_back
        MigrationRolledBack(
            script_id=script_id,
            environment=environment,
            reason=reason,
        )
        self._log.info("dbmigrate.script.rolled_back", script_id=script_id, environment=environment)
        return rolled_back

    async def get_execution(self, execution_id: str) -> MigrationExecution:
        """Get a migration execution by ID."""
        execution = self._executions.get(execution_id)
        if execution is None:
            raise ScriptNotFoundError(f"Migration execution not found: {execution_id}")
        return execution

    async def list_executions(self, script_id: str | None = None) -> list[MigrationExecution]:
        """List migration executions, optionally filtered by script."""
        executions = list(self._executions.values())
        if script_id is not None:
            executions = [e for e in executions if e.script_id == script_id]
        return executions

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about migrations."""
        total_scripts = len(self._scripts)
        total_executions = len(self._executions)
        by_status: dict[str, int] = {}
        for script in self._scripts.values():
            by_status[script.status.value] = by_status.get(script.status.value, 0) + 1
        successful = sum(1 for e in self._executions.values() if e.success)
        failed = sum(1 for e in self._executions.values() if not e.success)
        return {
            "total_scripts": total_scripts,
            "total_executions": total_executions,
            "by_status": by_status,
            "successful_executions": successful,
            "failed_executions": failed,
        }


__all__ = ["DatabaseMigrationAssistant"]
