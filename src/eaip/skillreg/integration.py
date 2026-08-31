"""Skill registry runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.skillreg.health import SkillRegistryHealthCheck

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SkillRegistryRuntimeModule:
    name: str = "skillreg"

    def __init__(self) -> None:
        self._health_check = SkillRegistryHealthCheck()
        self._log = get_logger("eaip.skillreg.integration")

    @property
    def health_check(self) -> SkillRegistryHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("skillreg.module.starting")
        kernel.platform.health.register(self._health_check)
        self._log.info("skillreg.module.started")

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("skillreg.module.stopping")


__all__ = ["SkillRegistryRuntimeModule"]
