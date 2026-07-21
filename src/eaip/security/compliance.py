"""Compliance service — run mock compliance checks and generate reports."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from eaip.logging.context import get_logger
from eaip.security.events import ComplianceCheckCompleted
from eaip.security.exceptions import ComplianceCheckError
from eaip.security.models import (
    ComplianceControl,
    ComplianceFramework,
    ComplianceReport,
    ComplianceStatus,
    ControlStatus,
)
from eaip.shared.time import utc_now

logger = get_logger("eaip.security.compliance")

_CONTROLS: dict[ComplianceFramework, list[dict[str, Any]]] = {
    ComplianceFramework.SOC2: [
        {"id": "soc2-cc1", "name": "Control Environment", "category": "security"},
        {"id": "soc2-cc2", "name": "Risk Assessment", "category": "security"},
        {"id": "soc2-cc3", "name": "Information & Communication", "category": "communication"},
        {"id": "soc2-cc4", "name": "Monitoring Activities", "category": "monitoring"},
        {"id": "soc2-cc5", "name": "Control Activities", "category": "security"},
    ],
    ComplianceFramework.HIPAA: [
        {"id": "hipaa-1", "name": "Administrative Safeguards", "category": "administrative"},
        {"id": "hipaa-2", "name": "Physical Safeguards", "category": "physical"},
        {"id": "hipaa-3", "name": "Technical Safeguards", "category": "technical"},
        {"id": "hipaa-4", "name": "Organizational Requirements", "category": "organizational"},
        {"id": "hipaa-5", "name": "Policies & Procedures", "category": "administrative"},
    ],
    ComplianceFramework.GDPR: [
        {"id": "gdpr-1", "name": "Data Processing Records", "category": "data_governance"},
        {"id": "gdpr-2", "name": "Consent Management", "category": "consent"},
        {"id": "gdpr-3", "name": "Data Subject Rights", "category": "rights"},
        {"id": "gdpr-4", "name": "Breach Notification", "category": "incident_response"},
        {
            "id": "gdpr-5",
            "name": "Data Protection Impact Assessment",
            "category": "risk_management",
        },
    ],
    ComplianceFramework.PCI: [
        {"id": "pci-1", "name": "Firewall Configuration", "category": "network_security"},
        {"id": "pci-2", "name": "Access Control", "category": "access_control"},
        {"id": "pci-3", "name": "Encryption of Cardholder Data", "category": "data_protection"},
        {"id": "pci-4", "name": "Vulnerability Management", "category": "vulnerability"},
        {"id": "pci-5", "name": "Monitoring & Testing", "category": "monitoring"},
    ],
}


class ComplianceService:
    """Runs compliance checks and generates reports for supported frameworks."""

    def __init__(self) -> None:
        self._reports: dict[str, ComplianceReport] = {}
        self._controls: dict[str, ComplianceControl] = {}
        self._event_log: list[Any] = []

    async def run_compliance_check(self, framework: ComplianceFramework) -> ComplianceReport:
        if framework not in list(ComplianceFramework):
            raise ComplianceCheckError(f"Unsupported framework: {framework}")

        control_defs = _CONTROLS.get(framework, [])
        controls: list[ComplianceControl] = []
        passed = 0

        for cdef in control_defs:
            ctrl = self._controls.get(cdef["id"])
            if ctrl is None:
                ctrl = ComplianceControl(
                    id=cdef["id"],
                    name=cdef["name"],
                    description=f"{framework.value} control: {cdef['name']}",
                    category=cdef["category"],
                    status=ControlStatus.PASS,
                    score=1.0,
                    tested_at=utc_now(),
                )
                self._controls[cdef["id"]] = ctrl
            if ctrl.status is ControlStatus.PASS:
                passed += 1
            controls.append(ctrl)

        total = len(controls)
        score = (passed / total * 100) if total > 0 else 0.0
        status = ComplianceStatus.PASS if score >= 80 else ComplianceStatus.FAIL

        report_id = str(uuid.uuid4())
        period_end = utc_now()
        period_start = period_end - timedelta(days=30)
        report = ComplianceReport(
            id=report_id,
            framework=framework,
            status=status,
            controls=tuple(controls),
            score=score,
            generated_at=period_end,
            period_start=period_start,
            period_end=period_end,
        )
        self._reports[report_id] = report
        self._event_log.append(
            ComplianceCheckCompleted(
                framework=framework.value,
                report_id=report_id,
                status=status.value,
                score=score,
                control_count=total,
            )
        )
        logger.info(
            "compliance_check_completed",
            framework=framework.value,
            status=status.value,
            score=score,
        )
        return report

    async def get_compliance_report(
        self, framework: ComplianceFramework
    ) -> ComplianceReport | None:
        for report in self._reports.values():
            if report.framework == framework:
                return report
        return None

    async def list_frameworks(self) -> list[ComplianceFramework]:
        return list(ComplianceFramework)

    async def get_control_status(self, control_id: str) -> ComplianceControl | None:
        return self._controls.get(control_id)

    async def update_control_evidence(
        self, control_id: str, evidence: dict[str, Any]
    ) -> ComplianceControl:
        ctrl = self._controls.get(control_id)
        if ctrl is None:
            raise ComplianceCheckError(f"Control {control_id} not found")
        updated = ComplianceControl(
            id=ctrl.id,
            name=ctrl.name,
            description=ctrl.description,
            category=ctrl.category,
            status=ControlStatus.PASS,
            score=1.0,
            evidence={**ctrl.evidence, **evidence},
            tested_at=utc_now(),
        )
        self._controls[control_id] = updated
        logger.info("control_evidence_updated", control_id=control_id)
        return updated

    @property
    def event_log(self) -> list[Any]:
        return self._event_log
