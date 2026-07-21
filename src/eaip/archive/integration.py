"""Runtime module integration for the archival subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.archive.health import ArchiveHealthCheck
from eaip.archive.manager import ArchiveManager
from eaip.archive.models import ArchiveConfig
from eaip.archive.store import LocalArchiveStore
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ArchiveRuntimeModule:
    """Runtime module that wires the archive subsystem into the kernel."""

    name: str = "archive"

    def __init__(
        self,
        config: ArchiveConfig | None = None,
        manager: ArchiveManager | None = None,
    ) -> None:
        """Initialize the runtime module with optional config and manager."""
        self._config = config or ArchiveConfig()
        self._store = LocalArchiveStore(base_path="./archive")
        self._manager = manager or ArchiveManager(config=self._config, store=self._store)
        self._log = get_logger("eaip.archive.integration")

    @property
    def manager(self) -> ArchiveManager:
        """Return the underlying ArchiveManager instance."""
        return self._manager

    async def start(self, kernel: RuntimeKernel) -> None:
        """Start the archive runtime module and register capability and health check."""
        self._log.info("archive.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.archive",
            title="Data Archival & Lifecycle Management",
            description="Archive, restore, and manage data retention policies",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("archive", "retention", "lifecycle", "cleanup"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ArchiveHealthCheck())
        self._log.info("archive.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Stop the archive runtime module."""
        self._log.info("archive.module.stopping")


__all__ = ["ArchiveRuntimeModule"]
