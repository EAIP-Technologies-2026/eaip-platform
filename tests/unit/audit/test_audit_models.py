"""Tests for audit models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eaip.audit.models import (
    ActorType,
    AuditConfig,
    AuditEvent,
    AuditLevel,
    AuditPolicy,
    ClassificationLevel,
    ComplianceReport,
    ComplianceStatus,
    DataClassification,
    LegalHold,
    LegalHoldStatus,
    RetentionAction,
    RetentionRule,
    Severity,
)


class TestAuditEvent:
    def test_minimal(self) -> None:
        e = AuditEvent(
            id="evt1",
            event_type="user.login",
            actor_id="user-1",
            actor_type=ActorType.USER,
            action="login",
            resource_type="session",
            resource_id="sess-1",
        )
        assert e.id == "evt1"
        assert e.severity == Severity.INFO
        assert e.target_id == ""
        assert e.details == {}
        assert e.tags == ()

    def test_frozen(self) -> None:
        e = AuditEvent(
            id="evt1",
            event_type="test",
            actor_id="a",
            actor_type=ActorType.SYSTEM,
            action="act",
            resource_type="rt",
            resource_id="ri",
        )
        with pytest.raises(ValidationError):
            e.action = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AuditEvent(
                id="evt1",
                event_type="test",
                actor_id="a",
                actor_type=ActorType.SYSTEM,
                action="act",
                resource_type="rt",
                resource_id="ri",
                unknown=True,
            )

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        e = AuditEvent(
            id="evt1",
            event_type="data.update",
            actor_id="user-1",
            actor_type=ActorType.USER,
            action="update",
            resource_type="document",
            resource_id="doc-123",
            target_id="field-1",
            details={"field": "name"},
            change_summary={"before": "old", "after": "new"},
            old_value="old",
            new_value="new",
            timestamp=ts,
            correlation_id="corr-1",
            ip_address="10.0.0.1",
            user_agent="test-client",
            session_id="sess-1",
            severity=Severity.HIGH,
            tags=("sensitive", "pii"),
            metadata={"env": "prod"},
        )
        assert e.target_id == "field-1"
        assert e.change_summary == {"before": "old", "after": "new"}
        assert e.old_value == "old"
        assert e.new_value == "new"
        assert e.timestamp == ts
        assert e.correlation_id == "corr-1"
        assert e.ip_address == "10.0.0.1"
        assert e.user_agent == "test-client"
        assert e.session_id == "sess-1"
        assert e.severity == Severity.HIGH
        assert e.tags == ("sensitive", "pii")
        assert e.metadata == {"env": "prod"}

    def test_all_actor_types(self) -> None:
        for at in ActorType:
            e = AuditEvent(
                id="evt1",
                event_type="t",
                actor_id="a",
                actor_type=at,
                action="act",
                resource_type="rt",
                resource_id="ri",
            )
            assert e.actor_type == at

    def test_all_severities(self) -> None:
        for s in Severity:
            e = AuditEvent(
                id="evt1",
                event_type="t",
                actor_id="a",
                actor_type=ActorType.SYSTEM,
                action="act",
                resource_type="rt",
                resource_id="ri",
                severity=s,
            )
            assert e.severity == s


class TestAuditPolicy:
    def test_minimal(self) -> None:
        p = AuditPolicy(id="p1", name="Default Policy")
        assert p.retention_days == 90
        assert p.storage_backend == "memory"
        assert p.encryption_enabled is True
        assert p.enabled is True

    def test_frozen(self) -> None:
        p = AuditPolicy(id="p1", name="P1")
        with pytest.raises(ValidationError):
            p.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AuditPolicy(id="p1", name="P1", bad=True)

    def test_full(self) -> None:
        p = AuditPolicy(
            id="p1",
            name="Full Policy",
            event_types=("user.login", "data.update"),
            retention_days=365,
            storage_backend="s3",
            encryption_enabled=False,
            notify_on_events=("data.update",),
            enabled=False,
            metadata={"owner": "security"},
        )
        assert p.event_types == ("user.login", "data.update")
        assert p.retention_days == 365
        assert p.storage_backend == "s3"
        assert p.encryption_enabled is False
        assert p.notify_on_events == ("data.update",)
        assert p.enabled is False
        assert p.metadata == {"owner": "security"}


class TestDataClassification:
    def test_minimal(self) -> None:
        dc = DataClassification(id="dc1", name="General", level=ClassificationLevel.INTERNAL)
        assert dc.retention_days == 90
        assert dc.rules == ()

    def test_frozen(self) -> None:
        dc = DataClassification(id="dc1", name="D1", level=ClassificationLevel.PUBLIC)
        with pytest.raises(ValidationError):
            dc.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DataClassification(id="dc1", name="D1", level=ClassificationLevel.PUBLIC, bad=True)

    def test_all_levels(self) -> None:
        for lvl in ClassificationLevel:
            dc = DataClassification(id=lvl.value, name=lvl.value, level=lvl)
            assert dc.level == lvl

    def test_full(self) -> None:
        dc = DataClassification(
            id="dc1",
            name="PII Data",
            level=ClassificationLevel.RESTRICTED,
            rules=("mask", "encrypt"),
            retention_days=365,
            handling_instructions="Store with encryption at rest",
            metadata={"owner": "dpo"},
        )
        assert dc.rules == ("mask", "encrypt")
        assert dc.retention_days == 365
        assert dc.handling_instructions == "Store with encryption at rest"
        assert dc.metadata == {"owner": "dpo"}


class TestRetentionRule:
    def test_minimal(self) -> None:
        r = RetentionRule(
            id="r1",
            name="Log Retention",
            data_type="logs",
            retention_period_days=90,
            action_on_expiry=RetentionAction.DELETE,
        )
        assert r.legal_hold_ids == ()
        assert r.enabled is True

    def test_frozen(self) -> None:
        r = RetentionRule(
            id="r1",
            name="R1",
            data_type="logs",
            retention_period_days=90,
            action_on_expiry=RetentionAction.DELETE,
        )
        with pytest.raises(ValidationError):
            r.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            RetentionRule(
                id="r1",
                name="R1",
                data_type="logs",
                retention_period_days=90,
                action_on_expiry=RetentionAction.DELETE,
                bad=True,
            )

    def test_all_actions(self) -> None:
        for act in RetentionAction:
            r = RetentionRule(
                id=act.value,
                name=act.value,
                data_type="t",
                retention_period_days=30,
                action_on_expiry=act,
            )
            assert r.action_on_expiry == act

    def test_full(self) -> None:
        r = RetentionRule(
            id="r1",
            name="Audit Log Retention",
            data_type="audit_logs",
            retention_period_days=365,
            action_on_expiry=RetentionAction.ARCHIVE,
            legal_hold_ids=("lh1",),
            enabled=False,
            metadata={"owner": "compliance"},
        )
        assert r.legal_hold_ids == ("lh1",)
        assert r.enabled is False
        assert r.metadata == {"owner": "compliance"}


class TestLegalHold:
    def test_minimal(self) -> None:
        lh = LegalHold(id="lh1", name="Investigation Hold", reason="Legal investigation")
        assert lh.status == LegalHoldStatus.ACTIVE
        assert lh.affected_data_types == ()

    def test_frozen(self) -> None:
        lh = LegalHold(id="lh1", name="LH1", reason="Test")
        with pytest.raises(ValidationError):
            lh.name = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            LegalHold(id="lh1", name="LH1", reason="Test", bad=True)

    def test_all_statuses(self) -> None:
        for st in LegalHoldStatus:
            lh = LegalHold(id=st.value, name=st.value, reason="R", status=st)
            assert lh.status == st

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        lh = LegalHold(
            id="lh1",
            name="Regulatory Hold",
            reason="GDPR request",
            affected_data_types=("pii", "financial"),
            affected_resources=("doc-1", "doc-2"),
            start_date=ts,
            end_date=ts,
            status=LegalHoldStatus.ACTIVE,
            created_by="user-1",
            metadata={"case": "CASE-001"},
        )
        assert lh.affected_data_types == ("pii", "financial")
        assert lh.affected_resources == ("doc-1", "doc-2")
        assert lh.start_date == ts
        assert lh.end_date == ts
        assert lh.created_by == "user-1"
        assert lh.metadata == {"case": "CASE-001"}


class TestComplianceReport:
    def test_minimal(self) -> None:
        cr = ComplianceReport(id="cr1", framework="SOC2", status=ComplianceStatus.IN_PROGRESS)
        assert cr.findings == ()
        assert cr.score == 0.0

    def test_frozen(self) -> None:
        cr = ComplianceReport(id="cr1", framework="SOC2", status=ComplianceStatus.PASS)
        with pytest.raises(ValidationError):
            cr.framework = "changed"

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ComplianceReport(id="cr1", framework="SOC2", status=ComplianceStatus.PASS, bad=True)

    def test_all_statuses(self) -> None:
        for st in ComplianceStatus:
            cr = ComplianceReport(id=st.value, framework="SOC2", status=st)
            assert cr.status == st

    def test_full(self) -> None:
        ts = datetime.now(UTC)
        findings = ({"control": "A1", "result": "pass"},)
        cr = ComplianceReport(
            id="cr1",
            framework="HIPAA",
            status=ComplianceStatus.PASS,
            findings=findings,
            score=95.5,
            generated_at=ts,
            period_start=ts,
            period_end=ts,
            metadata={"auditor": "external"},
        )
        assert cr.findings == findings
        assert cr.score == 95.5
        assert cr.period_start == ts
        assert cr.period_end == ts
        assert cr.metadata == {"auditor": "external"}


class TestAuditConfig:
    def test_defaults(self) -> None:
        c = AuditConfig()
        assert c.enable_immutable_log is True
        assert c.retention_default_days == 90
        assert c.encryption_enabled is True
        assert c.max_batch_size == 100
        assert c.enable_legal_hold is True
        assert c.audit_level == AuditLevel.DETAILED

    def test_custom(self) -> None:
        c = AuditConfig(
            enable_immutable_log=False,
            retention_default_days=365,
            encryption_enabled=False,
            max_batch_size=500,
            enable_legal_hold=False,
            audit_level=AuditLevel.FULL,
        )
        assert c.enable_immutable_log is False
        assert c.retention_default_days == 365
        assert c.encryption_enabled is False
        assert c.max_batch_size == 500
        assert c.enable_legal_hold is False
        assert c.audit_level == AuditLevel.FULL

    def test_frozen(self) -> None:
        c = AuditConfig()
        with pytest.raises(ValidationError):
            c.enable_immutable_log = False

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            AuditConfig(unknown=True)

    def test_all_audit_levels(self) -> None:
        for lvl in AuditLevel:
            c = AuditConfig(audit_level=lvl)
            assert c.audit_level == lvl
