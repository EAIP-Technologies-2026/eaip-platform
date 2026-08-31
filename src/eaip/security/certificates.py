"""Certificate manager — register, validate, and track certificates."""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.security.events import CertificateExpiring, CertificateRegistered, CertificateRevoked
from eaip.security.exceptions import CertificateExpiredError, CertificateNotFoundError
from eaip.security.models import Certificate
from eaip.shared.time import utc_now

logger = get_logger("eaip.security.certificates")


class CertificateManager:
    """Manages certificate lifecycle — registration, validation, expiry tracking."""

    def __init__(self) -> None:
        self._certificates: dict[str, Certificate] = {}
        self._revoked: set[str] = set()
        self._event_log: list[Any] = []

    async def register_certificate(self, cert: Certificate) -> str:
        self._certificates[cert.id] = cert
        self._event_log.append(
            CertificateRegistered(certificate_id=cert.id, certificate_name=cert.name)
        )
        logger.info("certificate_registered", cert_id=cert.id, name=cert.name)
        return cert.id

    async def get_certificate(self, cert_id: str) -> Certificate:
        cert = self._certificates.get(cert_id)
        if cert is None:
            raise CertificateNotFoundError(f"Certificate {cert_id} not found")
        return cert

    async def validate_certificate(self, cert_id: str) -> bool:
        cert = await self.get_certificate(cert_id)
        if cert_id in self._revoked:
            raise CertificateExpiredError(f"Certificate {cert_id} has been revoked")
        if not cert.enabled:
            raise CertificateExpiredError(f"Certificate {cert_id} is disabled")
        if cert.not_after is not None and cert.not_after <= utc_now():
            raise CertificateExpiredError(f"Certificate {cert_id} has expired at {cert.not_after}")
        if cert.not_before is not None and cert.not_before > utc_now():
            raise CertificateExpiredError(
                f"Certificate {cert_id} is not yet valid (not before {cert.not_before})"
            )
        return True

    async def list_certificates(self, expiring_within_days: int | None = None) -> list[Certificate]:
        now = utc_now()
        results: list[Certificate] = []
        for cert_id, cert in self._certificates.items():
            if cert_id in self._revoked:
                continue
            if expiring_within_days is not None:
                if cert.not_after is None:
                    continue
                days_left = (cert.not_after - now).days
                if days_left > expiring_within_days:
                    continue
            results.append(cert)
        return results

    async def revoke_certificate(self, cert_id: str) -> None:
        cert = await self.get_certificate(cert_id)
        self._revoked.add(cert_id)
        self._event_log.append(
            CertificateRevoked(certificate_id=cert_id, certificate_name=cert.name)
        )
        logger.info("certificate_revoked", cert_id=cert_id, name=cert.name)

    async def check_expiry(self) -> list[tuple[Certificate, int]]:
        now = utc_now()
        expiring: list[tuple[Certificate, int]] = []
        for cert in self._certificates.values():
            if cert.not_after is None:
                continue
            days_remaining = (cert.not_after - now).days
            if days_remaining <= 30:
                expiring.append((cert, days_remaining))
                self._event_log.append(
                    CertificateExpiring(
                        certificate_id=cert.id,
                        certificate_name=cert.name,
                        expires_at=cert.not_after,
                        days_remaining=days_remaining,
                    )
                )
                logger.warning(
                    "certificate_expiring",
                    cert_id=cert.id,
                    name=cert.name,
                    days_remaining=days_remaining,
                )
        return expiring

    def is_revoked(self, cert_id: str) -> bool:
        return cert_id in self._revoked

    @property
    def event_log(self) -> list[Any]:
        return self._event_log
