"""JSON schema runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.jsonschema.health import SchemaHealthCheck
from eaip.jsonschema.models import SchemaConfig
from eaip.jsonschema.service import JSONSchemaService
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SchemaRuntimeModule:
    name: str = "jsonschema"

    def __init__(
        self,
        config: SchemaConfig | None = None,
        service: JSONSchemaService | None = None,
    ) -> None:
        self._config = config or SchemaConfig()
        self._service = service or JSONSchemaService(config=self._config)
        self._health_check = SchemaHealthCheck(self._service)
        self._log = get_logger("eaip.jsonschema.integration")

    @property
    def config(self) -> SchemaConfig:
        return self._config

    @property
    def service(self) -> JSONSchemaService:
        return self._service

    @property
    def health_check(self) -> SchemaHealthCheck:
        return self._health_check

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("jsonschema.module.starting")
        platform = kernel.platform

        capability = Capability(
            name="eaip.jsonschema",
            title="JSON Schema Service",
            description="Schema document management, validation, and lifecycle",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("json", "schema", "validation", "document"),
        )
        platform.capabilities.register(capability)
        platform.health.register(self._health_check)
        kernel.register_module("jsonschema.service", self._service)
        self._log.info("jsonschema.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("jsonschema.module.stopping")


__all__ = ["SchemaRuntimeModule"]
