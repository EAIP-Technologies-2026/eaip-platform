"""Compliance report generator — run scans and report findings."""

from __future__ import annotations

from eaip.compliancegen.models import (
    ComplianceFinding,
    ComplianceFramework,
    ComplianceScan,
    GeneratorConfig,
)
from eaip.logging.context import get_logger


class ComplianceReportGenerator:
    """Service for generating compliance reports against frameworks."""

    def __init__(self, config: GeneratorConfig | None = None) -> None:
        self._config = config or GeneratorConfig()
        self._frameworks: dict[str, ComplianceFramework] = {}
        self._scans: dict[str, ComplianceScan] = {}
        self._findings: dict[str, ComplianceFinding] = {}
        self._log = get_logger("eaip.compliancegen.generator")

    @property
    def config(self) -> GeneratorConfig:
        return self._config

    async def register_framework(self, framework: ComplianceFramework) -> ComplianceFramework:
        self._frameworks[framework.id] = framework
        self._log.info("framework.registered", framework_id=framework.id)
        return framework

    async def get_framework(self, framework_id: str) -> ComplianceFramework | None:
        return self._frameworks.get(framework_id)

    async def start_scan(self, scan: ComplianceScan) -> ComplianceScan:
        self._scans[scan.id] = scan
        self._log.info("scan.started", scan_id=scan.id)
        return scan

    async def get_scan(self, scan_id: str) -> ComplianceScan | None:
        return self._scans.get(scan_id)

    async def add_finding(self, finding: ComplianceFinding) -> ComplianceFinding:
        self._findings[finding.id] = finding
        self._log.info("finding.added", finding_id=finding.id, scan_id=finding.scan_id)
        return finding

    async def get_findings_for_scan(self, scan_id: str) -> list[ComplianceFinding]:
        return [f for f in self._findings.values() if f.scan_id == scan_id]
