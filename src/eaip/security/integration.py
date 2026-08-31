"""Runtime integration — SecurityRuntimeModule for the EAIP kernel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.logging.context import get_logger
from eaip.security.certificates import CertificateManager
from eaip.security.compliance import ComplianceService
from eaip.security.crypto import EncryptionService
from eaip.security.health import SecurityHealthCheck
from eaip.security.vault import SecretVault

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel

logger = get_logger("eaip.security.integration")


class SecurityRuntimeModule:
    """Runtime module that starts and stops security services."""

    name: str = "security"

    def __init__(
        self,
        vault: SecretVault | None = None,
        crypto: EncryptionService | None = None,
        cert_manager: CertificateManager | None = None,
        compliance: ComplianceService | None = None,
    ) -> None:
        self._vault = vault or SecretVault()
        self._crypto = crypto or EncryptionService()
        self._cert_manager = cert_manager or CertificateManager()
        self._compliance = compliance or ComplianceService()
        self._health_check = SecurityHealthCheck(
            vault=self._vault,
            crypto=self._crypto,
            cert_manager=self._cert_manager,
            compliance=self._compliance,
        )

    async def start(self, kernel: RuntimeKernel) -> None:
        platform = kernel.platform
        platform.health.register(self._health_check)
        logger.info(
            "security_module_started",
            vault_ready=True,
            crypto_ready=True,
            cert_manager_ready=True,
            compliance_ready=True,
        )

    async def stop(self, kernel: RuntimeKernel) -> None:
        logger.info("security_module_stopped")

    @property
    def vault(self) -> SecretVault:
        return self._vault

    @property
    def crypto(self) -> EncryptionService:
        return self._crypto

    @property
    def cert_manager(self) -> CertificateManager:
        return self._cert_manager

    @property
    def compliance(self) -> ComplianceService:
        return self._compliance

    @property
    def health_check(self) -> SecurityHealthCheck:
        return self._health_check
