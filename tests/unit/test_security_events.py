"""Tests for :mod:`eaip.security.events`."""

from __future__ import annotations

import pytest

from eaip.events.event import DomainEvent
from eaip.security.events import (
    CertificateExpiring,
    CertificateRegistered,
    CertificateRevoked,
    ComplianceCheckCompleted,
    FindingStatusChanged,
    KeyGenerated,
    KeyRotated,
    SecretAccessed,
    SecretExpired,
    SecretRotated,
    SecretStored,
    SecurityFindingCreated,
)


class TestSecretStored:
    def test_defaults(self) -> None:
        e = SecretStored(secret_id="s1", secret_name="test", secret_type="api_key")
        assert isinstance(e, DomainEvent)
        assert e.event_type == "eaip.security.secret.stored"
        assert e.secret_id == "s1"

    def test_frozen(self) -> None:
        e = SecretStored(secret_id="s1", secret_name="n", secret_type="t")
        with pytest.raises((ValueError, TypeError)):
            e.secret_id = "s2"  # type: ignore[misc]


class TestSecretAccessed:
    def test_defaults(self) -> None:
        e = SecretAccessed(secret_id="s1", secret_name="test")
        assert e.event_type == "eaip.security.secret.accessed"
        assert e.secret_name == "test"


class TestSecretRotated:
    def test_defaults(self) -> None:
        e = SecretRotated(secret_id="s1", secret_name="test", new_version=2, previous_version=1)
        assert e.event_type == "eaip.security.secret.rotated"
        assert e.new_version == 2
        assert e.previous_version == 1


class TestSecretExpired:
    def test_defaults(self) -> None:
        e = SecretExpired(secret_id="s1", secret_name="test")
        assert e.event_type == "eaip.security.secret.expired"
        assert e.secret_id == "s1"


class TestKeyGenerated:
    def test_defaults(self) -> None:
        e = KeyGenerated(key_id="k1", key_name="key-1", algorithm="aes256", key_size=256)
        assert e.event_type == "eaip.security.key.generated"
        assert e.algorithm == "aes256"
        assert e.key_size == 256


class TestKeyRotated:
    def test_defaults(self) -> None:
        e = KeyRotated(key_id="k1", key_name="key-1", new_key_id="k2")
        assert e.event_type == "eaip.security.key.rotated"
        assert e.new_key_id == "k2"


class TestCertificateRegistered:
    def test_defaults(self) -> None:
        e = CertificateRegistered(certificate_id="c1", certificate_name="cert-1")
        assert e.event_type == "eaip.security.certificate.registered"
        assert e.certificate_id == "c1"


class TestCertificateExpiring:
    def test_defaults(self) -> None:
        e = CertificateExpiring(
            certificate_id="c1", certificate_name="cert-1", expires_at=None, days_remaining=5
        )
        assert e.event_type == "eaip.security.certificate.expiring"
        assert e.days_remaining == 5


class TestCertificateRevoked:
    def test_defaults(self) -> None:
        e = CertificateRevoked(certificate_id="c1", certificate_name="cert-1")
        assert e.event_type == "eaip.security.certificate.revoked"
        assert e.certificate_id == "c1"


class TestComplianceCheckCompleted:
    def test_defaults(self) -> None:
        e = ComplianceCheckCompleted(framework="soc2", report_id="r1", status="pass")
        assert e.event_type == "eaip.security.compliance.check_completed"
        assert e.framework == "soc2"
        assert e.score is None

    def test_with_score(self) -> None:
        e = ComplianceCheckCompleted(
            framework="pci", report_id="r1", status="pass", score=95.0, control_count=5
        )
        assert e.score == 95.0
        assert e.control_count == 5


class TestSecurityFindingCreated:
    def test_defaults(self) -> None:
        e = SecurityFindingCreated(
            finding_id="f1", severity="high", title="XSS", finding_type="vuln"
        )
        assert e.event_type == "eaip.security.finding.created"
        assert e.severity == "high"
        assert e.finding_type == "vuln"


class TestFindingStatusChanged:
    def test_defaults(self) -> None:
        e = FindingStatusChanged(finding_id="f1", previous_status="open", new_status="fixed")
        assert e.event_type == "eaip.security.finding.status_changed"
        assert e.previous_status == "open"
        assert e.new_status == "fixed"


class TestAllEvents:
    def test_all_have_unique_event_types(self) -> None:
        events = [
            SecretStored,
            SecretAccessed,
            SecretRotated,
            SecretExpired,
            KeyGenerated,
            KeyRotated,
            CertificateRegistered,
            CertificateExpiring,
            CertificateRevoked,
            ComplianceCheckCompleted,
            SecurityFindingCreated,
            FindingStatusChanged,
        ]
        types = [e.event_type for e in events]
        assert len(types) == len(set(types))

    def test_all_are_domain_events(self) -> None:
        events = [
            SecretStored(secret_id="s1", secret_name="n", secret_type="t"),
            SecretAccessed(secret_id="s1", secret_name="n"),
            SecretRotated(secret_id="s1", secret_name="n", new_version=2, previous_version=1),
            SecretExpired(secret_id="s1", secret_name="n"),
            KeyGenerated(key_id="k1", key_name="n", algorithm="a", key_size=256),
            KeyRotated(key_id="k1", key_name="n", new_key_id="k2"),
            CertificateRegistered(certificate_id="c1", certificate_name="n"),
            CertificateExpiring(
                certificate_id="c1", certificate_name="n", expires_at=None, days_remaining=5
            ),
            CertificateRevoked(certificate_id="c1", certificate_name="n"),
            ComplianceCheckCompleted(framework="soc2", report_id="r1", status="pass"),
            SecurityFindingCreated(finding_id="f1", severity="low", title="t", finding_type="v"),
            FindingStatusChanged(finding_id="f1", previous_status="open", new_status="fixed"),
        ]
        for e in events:
            assert isinstance(e, DomainEvent), f"{type(e).__name__} is not a DomainEvent"
