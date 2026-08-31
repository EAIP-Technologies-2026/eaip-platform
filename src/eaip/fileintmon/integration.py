"""File integrity monitor runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.fileintmon.health import FileIntegrityHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FileIntegrityRuntimeModule:
    """Runtime module for file integrity monitoring."""

    name: str = "fileintmon"

    def __init__(self) -> None:
        self._health_check = FileIntegrityHealthCheck()
        self._log = get_logger("eaip.fileintmon.integration")

    @property
    def health_check(self) -> FileIntegrityHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("fileintmon.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("fileintmon.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("fileintmon.module.stopping")


__all__ = ["FileIntegrityRuntimeModule"]
