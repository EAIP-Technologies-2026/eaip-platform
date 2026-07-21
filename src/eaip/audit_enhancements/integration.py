"""Runtime module integration for the audit enhancements subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.audit_enhancements.health import AuditEnhancementHealthCheck
from eaip.audit_enhancements.models import AuditEnhancementConfig
from eaip.audit_enhancements.service import AuditEnhancementService
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AuditEnhancementRuntimeModule:
    name: str = "audit_enhancements"

    def __init__(
        self,
        config: AuditEnhancementConfig | None = None,
        service: AuditEnhancementService | None = None,
    ) -> None:
        self._config = config or AuditEnhancementConfig()
        self._service = service or AuditEnhancementService(self._config)
        self._log = get_logger("eaip.audit_enhancements.integration")

    @property
    def service(self) -> AuditEnhancementService:
        return self._service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("audit_enhancements.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.audit_enhancements",
            title="Audit Enhancements",
            description="Correlation, enrichment, aggregation, alerts, and streaming for audit events",  # noqa: E501
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=(
                "audit",
                "enhancements",
                "correlation",
                "enrichment",
                "aggregation",
                "alerts",
                "streaming",
            ),
        )
        platform.capabilities.register(capability)
        platform.health.register(AuditEnhancementHealthCheck(service=self._service))
        self._log.info("audit_enhancements.module.started")

    async def stop(self, _kernel: RuntimeKernel | None = None) -> None:
        self._log.info("audit_enhancements.module.stopping")


__all__ = ["AuditEnhancementRuntimeModule"]
