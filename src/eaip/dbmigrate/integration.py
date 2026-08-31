"""Database migration runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.dbmigrate.health import DatabaseMigrationHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class DatabaseMigrationRuntimeModule:
    """Runtime module for database migration management."""

    name: str = "dbmigrate"

    def __init__(self) -> None:
        """Initialize the database migration runtime module."""
        self._health_check = DatabaseMigrationHealthCheck()
        self._log = get_logger("eaip.dbmigrate.integration")

    @property
    def health_check(self) -> DatabaseMigrationHealthCheck:
        """Return the database migration health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("dbmigrate.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("dbmigrate.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("dbmigrate.module.stopping")


__all__ = ["DatabaseMigrationRuntimeModule"]
