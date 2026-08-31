"""Tests for :mod:`eaip.security.certificates`."""

from __future__ import annotations

from datetime import timedelta

import pytest

from eaip.security.certificates import CertificateManager
from eaip.security.events import CertificateExpiring, CertificateRegistered, CertificateRevoked
from eaip.security.exceptions import CertificateExpiredError, CertificateNotFoundError
from eaip.security.models import Certificate
from eaip.shared.time import utc_now


class TestCertificateManager:
    async def test_register_and_get(self) -> None:
        mgr = CertificateManager()
        cert = Certificate(id="c1", name="test-cert")
        await mgr.register_certificate(cert)
        retrieved = await mgr.get_certificate("c1")
        assert retrieved.id == "c1"
        assert retrieved.name == "test-cert"

    async def test_get_not_found(self) -> None:
        mgr = CertificateManager()
        with pytest.raises(CertificateNotFoundError):
            await mgr.get_certificate("nonexistent")

    async def test_validate_valid_certificate(self) -> None:
        mgr = CertificateManager()
        future = utc_now() + timedelta(days=365)
        past = utc_now() - timedelta(days=1)
        cert = Certificate(id="c1", name="valid", not_before=past, not_after=future)
        await mgr.register_certificate(cert)
        result = await mgr.validate_certificate("c1")
        assert result is True

    async def test_validate_expired_certificate(self) -> None:
        mgr = CertificateManager()
        past = utc_now() - timedelta(days=10)
        earlier = past - timedelta(days=365)
        cert = Certificate(id="c1", name="expired", not_before=earlier, not_after=past)
        await mgr.register_certificate(cert)
        with pytest.raises(CertificateExpiredError):
            await mgr.validate_certificate("c1")

    async def test_validate_not_yet_valid(self) -> None:
        mgr = CertificateManager()
        future = utc_now() + timedelta(days=10)
        far_future = utc_now() + timedelta(days=365)
        cert = Certificate(id="c1", name="future", not_before=future, not_after=far_future)
        await mgr.register_certificate(cert)
        with pytest.raises(CertificateExpiredError):
            await mgr.validate_certificate("c1")

    async def test_validate_revoked_certificate(self) -> None:
        mgr = CertificateManager()
        cert = Certificate(id="c1", name="revoked")
        await mgr.register_certificate(cert)
        await mgr.revoke_certificate("c1")
        with pytest.raises(CertificateExpiredError):
            await mgr.validate_certificate("c1")

    async def test_validate_disabled_certificate(self) -> None:
        mgr = CertificateManager()
        cert = Certificate(id="c1", name="disabled", enabled=False)
        await mgr.register_certificate(cert)
        with pytest.raises(CertificateExpiredError):
            await mgr.validate_certificate("c1")

    async def test_list_certificates(self) -> None:
        mgr = CertificateManager()
        await mgr.register_certificate(Certificate(id="c1", name="a"))
        await mgr.register_certificate(Certificate(id="c2", name="b"))
        certs = await mgr.list_certificates()
        assert len(certs) == 2

    async def test_list_certificates_excludes_revoked(self) -> None:
        mgr = CertificateManager()
        await mgr.register_certificate(Certificate(id="c1", name="a"))
        await mgr.register_certificate(Certificate(id="c2", name="b"))
        await mgr.revoke_certificate("c1")
        certs = await mgr.list_certificates()
        assert len(certs) == 1
        assert certs[0].id == "c2"

    async def test_list_certificates_expiring_within(self) -> None:
        mgr = CertificateManager()
        now = utc_now()
        await mgr.register_certificate(
            Certificate(id="c1", name="soon", not_after=now + timedelta(days=5))
        )
        await mgr.register_certificate(
            Certificate(id="c2", name="far", not_after=now + timedelta(days=100))
        )
        certs = await mgr.list_certificates(expiring_within_days=30)
        assert len(certs) == 1
        assert certs[0].id == "c1"

    async def test_revoke_certificate(self) -> None:
        mgr = CertificateManager()
        cert = Certificate(id="c1", name="test")
        await mgr.register_certificate(cert)
        await mgr.revoke_certificate("c1")
        assert mgr.is_revoked("c1") is True

    async def test_revoke_not_found(self) -> None:
        mgr = CertificateManager()
        with pytest.raises(CertificateNotFoundError):
            await mgr.revoke_certificate("nonexistent")

    async def test_check_expiry(self) -> None:
        mgr = CertificateManager()
        now = utc_now()
        await mgr.register_certificate(
            Certificate(id="c1", name="expiring", not_after=now + timedelta(days=5))
        )
        await mgr.register_certificate(
            Certificate(id="c2", name="ok", not_after=now + timedelta(days=365))
        )
        await mgr.register_certificate(Certificate(id="c3", name="no-expiry"))
        expiring = await mgr.check_expiry()
        assert len(expiring) == 1
        assert expiring[0][0].id == "c1"
        assert 0 < expiring[0][1] <= 5

    async def test_register_event_emitted(self) -> None:
        mgr = CertificateManager()
        await mgr.register_certificate(Certificate(id="c1", name="test"))
        assert any(isinstance(e, CertificateRegistered) for e in mgr.event_log)

    async def test_revoke_event_emitted(self) -> None:
        mgr = CertificateManager()
        await mgr.register_certificate(Certificate(id="c1", name="test"))
        await mgr.revoke_certificate("c1")
        assert any(isinstance(e, CertificateRevoked) for e in mgr.event_log)

    async def test_expiry_event_emitted(self) -> None:
        mgr = CertificateManager()
        now = utc_now()
        await mgr.register_certificate(
            Certificate(id="c1", name="expiring", not_after=now + timedelta(days=5))
        )
        await mgr.check_expiry()
        assert any(isinstance(e, CertificateExpiring) for e in mgr.event_log)
