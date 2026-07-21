"""Tests for :mod:`eaip.security.models`."""

from __future__ import annotations

import pytest

from eaip.security.models import (
    Certificate,
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    ComplianceStatus,
    ControlStatus,
    EncryptionAlgorithm,
    EncryptionKey,
    FindingSeverity,
    FindingStatus,
    ScanResult,
    ScanStatus,
    Secret,
    SecretType,
    SecurityConfig,
    SecurityFinding,
)


class TestSecret:
    def test_defaults(self) -> None:
        s = Secret(id="s1", name="test-key", type=SecretType.API_KEY, value="encrypted-value")
        assert s.id == "s1"
        assert s.name == "test-key"
        assert s.type is SecretType.API_KEY
        assert s.description == ""
        assert s.tags == ()
        assert s.version == 1
        assert s.enabled is True

    def test_with_all_fields(self) -> None:
        s = Secret(
            id="s2",
            name="db-pass",
            type=SecretType.PASSWORD,
            value="enc-pass",
            description="Database password",
            tags=("db", "prod"),
            metadata={"env": "prod"},
            version=2,
            enabled=False,
            rotation_period_days=30,
        )
        assert s.name == "db-pass"
        assert s.type is SecretType.PASSWORD
        assert "prod" in s.tags
        assert s.version == 2
        assert s.enabled is False
        assert s.rotation_period_days == 30

    def test_frozen(self) -> None:
        s = Secret(id="s1", name="k", type=SecretType.TOKEN, value="v")
        with pytest.raises((ValueError, TypeError)):
            s.name = "new-name"  # type: ignore[misc]

    def test_secret_type_values(self) -> None:
        assert SecretType.API_KEY.value == "api_key"
        assert SecretType.PASSWORD.value == "password"
        assert SecretType.CERTIFICATE.value == "certificate"
        assert SecretType.TOKEN.value == "token"
        assert SecretType.CREDENTIAL.value == "credential"


class TestEncryptionKey:
    def test_defaults(self) -> None:
        k = EncryptionKey(
            id="k1", name="my-key", algorithm=EncryptionAlgorithm.AES256, key_size=256
        )
        assert k.algorithm is EncryptionAlgorithm.AES256
        assert k.key_size == 256
        assert k.enabled is True
        assert k.metadata == {}

    def test_with_all_fields(self) -> None:
        k = EncryptionKey(
            id="k2",
            name="rsa-key",
            algorithm=EncryptionAlgorithm.RSA2048,
            key_size=2048,
            enabled=False,
            metadata={"purpose": "signing"},
        )
        assert k.algorithm is EncryptionAlgorithm.RSA2048
        assert k.enabled is False

    def test_frozen(self) -> None:
        k = EncryptionKey(id="k1", name="k", algorithm=EncryptionAlgorithm.ECC, key_size=256)
        with pytest.raises((ValueError, TypeError)):
            k.name = "new"  # type: ignore[misc]

    def test_algorithm_values(self) -> None:
        assert EncryptionAlgorithm.AES256.value == "aes256"
        assert EncryptionAlgorithm.RSA2048.value == "rsa2048"
        assert EncryptionAlgorithm.ECC.value == "ecc"


class TestCertificate:
    def test_defaults(self) -> None:
        c = Certificate(id="c1", name="test-cert")
        assert c.issuer == ""
        assert c.subject == ""
        assert c.enabled is True
        assert c.fingerprints == {}

    def test_with_all_fields(self) -> None:
        c = Certificate(
            id="c2",
            name="prod-cert",
            issuer="CA",
            subject="*.example.com",
            serial_number="12345",
            fingerprints={"sha256": "abc123"},
            pem_encoded="---BEGIN---",
            enabled=True,
            tags=("prod",),
        )
        assert c.issuer == "CA"
        assert c.fingerprints["sha256"] == "abc123"

    def test_frozen(self) -> None:
        c = Certificate(id="c1", name="c")
        with pytest.raises((ValueError, TypeError)):
            c.name = "new"  # type: ignore[misc]


class TestSecurityFinding:
    def test_defaults(self) -> None:
        f = SecurityFinding(
            id="f1", severity=FindingSeverity.HIGH, type="vuln", title="SQL Injection"
        )
        assert f.status is FindingStatus.OPEN
        assert f.cve is None
        assert f.cvss_score is None

    def test_with_all_fields(self) -> None:
        f = SecurityFinding(
            id="f2",
            severity=FindingSeverity.CRITICAL,
            type="cve",
            title="RCE",
            description="Remote code execution",
            location="/api/exec",
            remediation="Upgrade library",
            cve="CVE-2024-1234",
            cvss_score=9.8,
            status=FindingStatus.ACKNOWLEDGED,
        )
        assert f.cve == "CVE-2024-1234"
        assert f.cvss_score == 9.8
        assert f.status is FindingStatus.ACKNOWLEDGED

    def test_frozen(self) -> None:
        f = SecurityFinding(id="f1", severity=FindingSeverity.LOW, type="x", title="y")
        with pytest.raises((ValueError, TypeError)):
            f.title = "new"  # type: ignore[misc]

    def test_severity_values(self) -> None:
        assert FindingSeverity.INFO.value == "info"
        assert FindingSeverity.LOW.value == "low"
        assert FindingSeverity.MEDIUM.value == "medium"
        assert FindingSeverity.HIGH.value == "high"
        assert FindingSeverity.CRITICAL.value == "critical"

    def test_status_values(self) -> None:
        assert FindingStatus.OPEN.value == "open"
        assert FindingStatus.ACKNOWLEDGED.value == "acknowledged"
        assert FindingStatus.FIXED.value == "fixed"
        assert FindingStatus.FALSE_POSITIVE.value == "false_positive"


class TestScanResult:
    def test_defaults(self) -> None:
        s = ScanResult(id="sc1", scanner="trivy", target="app", status=ScanStatus.CLEAN)
        assert s.findings == ()
        assert s.duration_ms == 0.0

    def test_with_findings(self) -> None:
        f = SecurityFinding(id="f1", severity=FindingSeverity.MEDIUM, type="x", title="y")
        s = ScanResult(
            id="sc2", scanner="snyk", target="lib", status=ScanStatus.WARNING, findings=(f,)
        )
        assert len(s.findings) == 1
        assert s.findings[0].id == "f1"

    def test_frozen(self) -> None:
        s = ScanResult(id="sc1", scanner="x", target="y", status=ScanStatus.CLEAN)
        with pytest.raises((ValueError, TypeError)):
            s.status = ScanStatus.WARNING  # type: ignore[misc]

    def test_scan_status_values(self) -> None:
        assert ScanStatus.CLEAN.value == "clean"
        assert ScanStatus.WARNING.value == "warning"
        assert ScanStatus.ERROR.value == "error"
        assert ScanStatus.CRITICAL.value == "critical"


class TestComplianceControl:
    def test_defaults(self) -> None:
        c = ComplianceControl(id="cc1", name="Test Control")
        assert c.status is ControlStatus.NOT_TESTED
        assert c.score is None
        assert c.evidence == {}

    def test_with_values(self) -> None:
        c = ComplianceControl(
            id="cc2",
            name="Access Control",
            category="security",
            status=ControlStatus.PASS,
            score=1.0,
            evidence={"policy_doc": "url"},
        )
        assert c.score == 1.0
        assert c.evidence["policy_doc"] == "url"

    def test_frozen(self) -> None:
        c = ComplianceControl(id="cc1", name="c")
        with pytest.raises((ValueError, TypeError)):
            c.name = "new"  # type: ignore[misc]

    def test_control_status_values(self) -> None:
        assert ControlStatus.PASS.value == "pass"
        assert ControlStatus.FAIL.value == "fail"
        assert ControlStatus.NA.value == "na"
        assert ControlStatus.NOT_TESTED.value == "not_tested"


class TestComplianceReport:
    def test_defaults(self) -> None:
        r = ComplianceReport(
            id="r1", framework=ComplianceFramework.SOC2, status=ComplianceStatus.IN_PROGRESS
        )
        assert r.controls == ()
        assert r.score is None

    def test_with_controls(self) -> None:
        c = ComplianceControl(id="cc1", name="Ctrl", status=ControlStatus.PASS, score=1.0)
        r = ComplianceReport(
            id="r2",
            framework=ComplianceFramework.GDPR,
            status=ComplianceStatus.PASS,
            controls=(c,),
            score=100.0,
        )
        assert r.score == 100.0
        assert len(r.controls) == 1

    def test_frozen(self) -> None:
        r = ComplianceReport(
            id="r1", framework=ComplianceFramework.PCI, status=ComplianceStatus.FAIL
        )
        with pytest.raises((ValueError, TypeError)):
            r.status = ComplianceStatus.PASS  # type: ignore[misc]

    def test_framework_values(self) -> None:
        assert ComplianceFramework.SOC2.value == "soc2"
        assert ComplianceFramework.HIPAA.value == "hipaa"
        assert ComplianceFramework.GDPR.value == "gdpr"
        assert ComplianceFramework.PCI.value == "pci"

    def test_compliance_status_values(self) -> None:
        assert ComplianceStatus.PASS.value == "pass"
        assert ComplianceStatus.FAIL.value == "fail"
        assert ComplianceStatus.IN_PROGRESS.value == "in_progress"


class TestSecurityConfig:
    def test_defaults(self) -> None:
        c = SecurityConfig()
        assert c.key_rotation_enabled is True
        assert c.key_rotation_interval_days == 90
        assert c.audit_log_all_access is True
        assert c.enable_secret_expiry is True
        assert c.default_secret_ttl_days == 365
        assert c.max_failed_access_attempts == 5
        assert c.scan_timeout_seconds == 300

    def test_custom_values(self) -> None:
        c = SecurityConfig(
            key_rotation_enabled=False,
            key_rotation_interval_days=180,
            audit_log_all_access=False,
            enable_secret_expiry=False,
            default_secret_ttl_days=30,
            max_failed_access_attempts=3,
            scan_timeout_seconds=600,
        )
        assert c.key_rotation_enabled is False
        assert c.key_rotation_interval_days == 180
        assert c.scan_timeout_seconds == 600

    def test_frozen(self) -> None:
        c = SecurityConfig()
        with pytest.raises((ValueError, TypeError)):
            c.scan_timeout_seconds = 100  # type: ignore[misc]
