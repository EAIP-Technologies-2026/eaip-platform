"""Runtime module integration for the audit subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.audit.classification import DataClassifier
from eaip.audit.health import AuditHealthCheck
from eaip.audit.legal_hold import LegalHoldService
from eaip.audit.logger import AuditLogger
from eaip.audit.models import AuditConfig
from eaip.audit.policies import AuditPolicyService
from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class AuditRuntimeModule:
    name: str = "audit"

    def __init__(
        self,
        config: AuditConfig | None = None,
        logger: AuditLogger | None = None,
        policy_service: AuditPolicyService | None = None,
        classifier: DataClassifier | None = None,
        legal_hold_service: LegalHoldService | None = None,
    ) -> None:
        self._config = config or AuditConfig()
        self._logger = logger or AuditLogger()
        self._policy_service = policy_service or AuditPolicyService()
        self._classifier = classifier or DataClassifier()
        self._legal_hold_service = legal_hold_service or LegalHoldService()
        self._log = get_logger("eaip.audit.integration")

    @property
    def logger(self) -> AuditLogger:
        return self._logger

    @property
    def policy_service(self) -> AuditPolicyService:
        return self._policy_service

    @property
    def classifier(self) -> DataClassifier:
        return self._classifier

    @property
    def legal_hold_service(self) -> LegalHoldService:
        return self._legal_hold_service

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("audit.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.audit",
            title="Audit & Compliance",
            description="Immutable audit trail, data classification, retention policies, legal holds, and compliance reporting",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("audit", "compliance", "retention", "legal-hold", "classification"),
        )
        platform.capabilities.register(capability)
        platform.health.register(AuditHealthCheck(logger=self._logger))
        self._log.info("audit.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("audit.module.stopping")


__all__ = ["AuditRuntimeModule"]
