"""Security domain models — secrets, keys, certificates, scans, compliance."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class SecretType(StrEnum):
    API_KEY = "api_key"
    PASSWORD = "password"
    CERTIFICATE = "certificate"
    TOKEN = "token"
    CREDENTIAL = "credential"


class FindingSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    FIXED = "fixed"
    FALSE_POSITIVE = "false_positive"


class ScanStatus(StrEnum):
    CLEAN = "clean"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComplianceStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    IN_PROGRESS = "in_progress"


class ComplianceFramework(StrEnum):
    SOC2 = "soc2"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI = "pci"


class ControlStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NA = "na"
    NOT_TESTED = "not_tested"


class EncryptionAlgorithm(StrEnum):
    AES256 = "aes256"
    RSA2048 = "rsa2048"
    ECC = "ecc"


class Secret(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    type: SecretType
    value: str
    description: str = ""
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = Field(default=None)
    rotation_period_days: int | None = Field(default=None)
    version: int = Field(default=1)
    enabled: bool = Field(default=True)


class EncryptionKey(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    algorithm: EncryptionAlgorithm
    key_size: int
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = Field(default=None)
    enabled: bool = Field(default=True)
    metadata: dict[str, Any] = Field(default_factory=dict)
    rotation_due_at: datetime | None = Field(default=None)


class Certificate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    issuer: str = Field(default="")
    subject: str = Field(default="")
    serial_number: str = Field(default="")
    not_before: datetime | None = Field(default=None)
    not_after: datetime | None = Field(default=None)
    fingerprints: dict[str, str] = Field(default_factory=dict)
    pem_encoded: str = Field(default="")
    enabled: bool = Field(default=True)
    tags: tuple[str, ...] = Field(default=())
    metadata: dict[str, Any] = Field(default_factory=dict)


class SecurityFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    severity: FindingSeverity
    type: str
    title: str
    description: str = Field(default="")
    location: str = Field(default="")
    remediation: str = Field(default="")
    cve: str | None = Field(default=None)
    cvss_score: float | None = Field(default=None)
    status: FindingStatus = Field(default=FindingStatus.OPEN)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScanResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    scanner: str
    target: str
    status: ScanStatus
    findings: tuple[SecurityFinding, ...] = Field(default=())
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float = Field(default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComplianceControl(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str = Field(default="")
    category: str = Field(default="")
    status: ControlStatus = Field(default=ControlStatus.NOT_TESTED)
    score: float | None = Field(default=None)
    evidence: dict[str, Any] = Field(default_factory=dict)
    tested_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComplianceReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    framework: ComplianceFramework
    status: ComplianceStatus
    controls: tuple[ComplianceControl, ...] = Field(default=())
    score: float | None = Field(default=None)
    generated_at: datetime = Field(default_factory=utc_now)
    period_start: datetime | None = Field(default=None)
    period_end: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SecurityConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key_rotation_enabled: bool = Field(default=True)
    key_rotation_interval_days: int = Field(default=90)
    audit_log_all_access: bool = Field(default=True)
    enable_secret_expiry: bool = Field(default=True)
    default_secret_ttl_days: int = Field(default=365)
    max_failed_access_attempts: int = Field(default=5)
    scan_timeout_seconds: int = Field(default=300)
