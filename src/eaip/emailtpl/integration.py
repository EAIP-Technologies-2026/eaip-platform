"""Email template designer runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.emailtpl.health import TemplateDesignerHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class TemplateDesignerRuntimeModule:
    """Runtime module for the email template designer."""

    name: str = "emailtpl"

    def __init__(self) -> None:
        """Initialize the template designer runtime module."""
        self._health_check = TemplateDesignerHealthCheck()
        self._log = get_logger("eaip.emailtpl.integration")

    @property
    def health_check(self) -> TemplateDesignerHealthCheck:
        """Return the template designer health check instance."""
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        """Register the module with the kernel."""
        self._log.info("emailtpl.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("emailtpl.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        """Shut down the module."""
        self._log.info("emailtpl.module.stopping")


__all__ = ["TemplateDesignerRuntimeModule"]
