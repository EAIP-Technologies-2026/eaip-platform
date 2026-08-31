"""Security health check — reports on vault, crypto, certificates, compliance."""

from __future__ import annotations

from eaip.health.checks import HealthCheck, HealthReport, HealthStatus
from eaip.security.certificates import CertificateManager
from eaip.security.compliance import ComplianceService
from eaip.security.crypto import EncryptionService
from eaip.security.vault import SecretVault


class SecurityHealthCheck(HealthCheck):
    """Aggregate health check for security subsystems."""

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

    async def check(self) -> HealthReport:
        children: list[HealthReport] = []

        vault_report = await self._check_vault()
        children.append(vault_report)

        crypto_report = await self._check_crypto()
        children.append(crypto_report)

        cert_report = await self._check_certificates()
        children.append(cert_report)

        compliance_report = await self._check_compliance()
        children.append(compliance_report)

        statuses = [c.status.numeric for c in children]
        overall = max(statuses) if statuses else 0
        overall_status = HealthStatus(("healthy", "degraded", "unhealthy")[overall])

        return HealthReport(
            component=self.name,
            status=overall_status,
            message=f"Security subsystems: {overall_status.value}",
            children=tuple(children),
        )

    async def _check_vault(self) -> HealthReport:
        try:
            expired = await self._vault.check_expiry()
            if expired:
                return HealthReport(
                    component="vault",
                    status=HealthStatus.DEGRADED,
                    message=f"{len(expired)} expired secret(s) found",
                    details={"expired_count": len(expired)},
                )
            return HealthReport(
                component="vault",
                status=HealthStatus.HEALTHY,
                message="No expired secrets",
            )
        except Exception as exc:
            return HealthReport(
                component="vault",
                status=HealthStatus.UNHEALTHY,
                message=str(exc),
            )

    async def _check_crypto(self) -> HealthReport:
        try:
            keys = await self._crypto.list_keys()
            disabled = [k for k in keys if not k.enabled]
            if disabled:
                return HealthReport(
                    component="crypto",
                    status=HealthStatus.DEGRADED,
                    message=f"{len(disabled)} disabled key(s)",
                    details={"disabled_keys": len(disabled), "total_keys": len(keys)},
                )
            return HealthReport(
                component="crypto",
                status=HealthStatus.HEALTHY,
                message=f"{len(keys)} key(s) available",
            )
        except Exception as exc:
            return HealthReport(
                component="crypto",
                status=HealthStatus.UNHEALTHY,
                message=str(exc),
            )

    async def _check_certificates(self) -> HealthReport:
        try:
            expiring = await self._cert_manager.check_expiry()
            if expiring:
                return HealthReport(
                    component="certificates",
                    status=HealthStatus.DEGRADED,
                    message=f"{len(expiring)} certificate(s) expiring within 30 days",
                    details={"expiring_count": len(expiring)},
                )
            return HealthReport(
                component="certificates",
                status=HealthStatus.HEALTHY,
                message="No certificates expiring soon",
            )
        except Exception as exc:
            return HealthReport(
                component="certificates",
                status=HealthStatus.UNHEALTHY,
                message=str(exc),
            )

    async def _check_compliance(self) -> HealthReport:
        try:
            frameworks = await self._compliance.list_frameworks()
            return HealthReport(
                component="compliance",
                status=HealthStatus.HEALTHY,
                message=f"{len(frameworks)} framework(s) available",
                details={"frameworks": [f.value for f in frameworks]},
            )
        except Exception as exc:
            return HealthReport(
                component="compliance",
                status=HealthStatus.UNHEALTHY,
                message=str(exc),
            )
