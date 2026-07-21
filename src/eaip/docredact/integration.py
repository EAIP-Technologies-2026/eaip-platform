"""Document redaction runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.docredact.health import RedactionHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class RedactionRuntimeModule:
    """Runtime module for document redaction."""

    name: str = "docredact"

    def __init__(self) -> None:
        """Initialize the redaction runtime module."""
        self._health_check = RedactionHealthCheck()
        self._log = get_logger("eaip.docredact.integration")

    @property
    def health_check(self) -> RedactionHealthCheck:
        """Return the redaction health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("docredact.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("docredact.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("docredact.module.stopping")


__all__ = ["RedactionRuntimeModule"]
