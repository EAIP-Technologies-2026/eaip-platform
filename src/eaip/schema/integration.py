"""Runtime module integration for the schema registry subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger
from eaip.schema.compatibility import CompatibilityChecker
from eaip.schema.health import SchemaHealthCheck
from eaip.schema.models import SchemaConfig
from eaip.schema.registry import SchemaRegistry
from eaip.schema.validation import SchemaValidator

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class SchemaRuntimeModule:
    name: str = "schema"

    def __init__(
        self,
        config: SchemaConfig | None = None,
        registry: SchemaRegistry | None = None,
        validator: SchemaValidator | None = None,
        compatibility_checker: CompatibilityChecker | None = None,
    ) -> None:
        self._config = config or SchemaConfig()
        self._registry = registry or SchemaRegistry(config=self._config)
        self._validator = validator or SchemaValidator(registry=self._registry)
        self._compatibility_checker = compatibility_checker or CompatibilityChecker(
            registry=self._registry
        )
        self._log = get_logger("eaip.schema.integration")

    @property
    def registry(self) -> SchemaRegistry:
        return self._registry

    @property
    def validator(self) -> SchemaValidator:
        return self._validator

    @property
    def compatibility_checker(self) -> CompatibilityChecker:
        return self._compatibility_checker

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("schema.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.schema",
            title="Schema Registry",
            description="Schema management, validation, evolution, and compatibility checking for data contracts",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("schema", "registry", "validation", "compatibility", "evolution"),
        )
        platform.capabilities.register(capability)
        platform.health.register(SchemaHealthCheck(registry=self._registry))
        self._log.info("schema.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("schema.module.stopping")


__all__ = ["SchemaRuntimeModule"]
