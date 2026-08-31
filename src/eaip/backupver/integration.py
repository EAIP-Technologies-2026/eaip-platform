"""Backup verification runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.backupver.health import BackupVerificationHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class BackupVerificationRuntimeModule:
    """Runtime module for backup verification."""

    name: str = "backupver"

    def __init__(self) -> None:
        """Initialize the backup verification runtime module."""
        self._health_check = BackupVerificationHealthCheck()
        self._log = get_logger("eaip.backupver.integration")

    @property
    def health_check(self) -> BackupVerificationHealthCheck:
        """Return the backup verification health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("backupver.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("backupver.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("backupver.module.stopping")


__all__ = ["BackupVerificationRuntimeModule"]
