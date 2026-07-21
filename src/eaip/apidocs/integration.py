"""RuntimeKernel integration — registers DocGenerator as a RuntimeModule."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eaip.apidocs.changelog import DocChangelogService
from eaip.apidocs.generator import DocGenerator
from eaip.apidocs.health import ApiDocsHealthCheck
from eaip.apidocs.publisher import DocPublisher
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ApiDocsRuntimeModule:
    name: str = "apidocs"

    def __init__(
        self,
        generator: DocGenerator | None = None,
        publisher: DocPublisher | None = None,
        changelog: DocChangelogService | None = None,
        event_bus: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._generator = generator or DocGenerator(event_bus=event_bus)
        self._publisher = publisher or DocPublisher(event_bus=event_bus)
        self._changelog = changelog or DocChangelogService(event_bus=event_bus)
        self._health_check = ApiDocsHealthCheck()
        self._log = get_logger("eaip.apidocs.integration")

    @property
    def generator(self) -> DocGenerator:
        return self._generator

    @property
    def publisher(self) -> DocPublisher:
        return self._publisher

    @property
    def changelog(self) -> DocChangelogService:
        return self._changelog

    async def start(self, kernel: RuntimeKernel) -> None:
        t0 = time.monotonic()
        self._log.info("apidocs.module.start")

        kernel.platform.health.register(self._health_check)
        kernel.platform.capabilities.register(
            Capability(
                name="apidocs:generator",
                title="API Documentation Generator",
                status=CapabilityStatus.ENABLED,
                tags=("api", "docs", "openapi"),
            )
        )

        kernel.register_module("apidocs.generator", self._generator)
        kernel.register_module("apidocs.publisher", self._publisher)
        kernel.register_module("apidocs.changelog", self._changelog)

        self._log.info(
            "apidocs.module.complete",
            duration_s=round(time.monotonic() - t0, 3),
        )

    async def stop(self, _kernel: RuntimeKernel) -> None:
        self._log.info("apidocs.module.stop")


__all__ = ["ApiDocsRuntimeModule"]
