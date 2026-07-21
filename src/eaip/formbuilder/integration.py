"""Form builder runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.formbuilder.builder import FormBuilderService
from eaip.formbuilder.health import FormBuilderHealthCheck
from eaip.formbuilder.models import FormConfig
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class FormBuilderRuntimeModule:
    name: str = "formbuilder"

    def __init__(
        self,
        config: FormConfig | None = None,
        service: FormBuilderService | None = None,
    ) -> None:
        self._config = config or FormConfig()
        self._service = service or FormBuilderService(config=self._config)
        self._health_check = FormBuilderHealthCheck(self._service)
        self._log = get_logger("eaip.formbuilder.integration")

    @property
    def config(self) -> FormConfig:
        return self._config

    @property
    def service(self) -> FormBuilderService:
        return self._service

    @property
    def health_check(self) -> FormBuilderHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("formbuilder.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.formbuilder",
            title="Form Builder Service",
            description=("Form definition, submission, validation, and lifecycle management"),
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("form", "builder", "submission", "workflow"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("formbuilder.service", self._service)
        self._log.info("formbuilder.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("formbuilder.module.stopping")


__all__ = ["FormBuilderRuntimeModule"]
