"""Consent runtime module for kernel lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.consent.health import ConsentHealthCheck
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ConsentRuntimeModule:
    """Runtime module for consent and privacy management."""

    name: str = "consent"

    def __init__(self) -> None:
        self._health_check = ConsentHealthCheck()
        self._log = get_logger("eaip.consent.integration")

    @property
    def health_check(self) -> ConsentHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("consent.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("consent.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("consent.module.stopping")


__all__ = ["ConsentRuntimeModule"]
