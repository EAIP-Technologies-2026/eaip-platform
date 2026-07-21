"""DependencyScanner — scan targets and report vulnerabilities."""

from __future__ import annotations

from eaip.depscan.events import ScanCompleted, ScanStarted, VulnerabilityFound
from eaip.depscan.exceptions import TargetNotFoundError
from eaip.depscan.models import (
    ScanConfig,
    ScanResult,
    ScanTarget,
    Severity,
    Vulnerability,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class DependencyScanner:
    """Central service for scanning dependencies and tracking vulnerabilities."""

    def __init__(self, config: ScanConfig | None = None) -> None:
        self._config = config or ScanConfig()
        self._targets: dict[str, ScanTarget] = {}
        self._vulnerabilities: dict[str, Vulnerability] = {}
        self._results: dict[str, ScanResult] = {}
        self._log = get_logger("eaip.depscan.service")

    @property
    def config(self) -> ScanConfig:
        return self._config

    async def register_target(self, target: ScanTarget) -> ScanTarget:
        """Register a new scan target."""
        self._targets[target.id] = target
        self._log.info("depscan.target.registered", target_id=target.id, name=target.name)
        return target

    async def get_target(self, target_id: str) -> ScanTarget:
        """Get a scan target by ID."""
        target = self._targets.get(target_id)
        if target is None:
            raise TargetNotFoundError(f"Scan target not found: {target_id}")
        return target

    async def list_targets(self) -> list[ScanTarget]:
        """List all registered scan targets."""
        return list(self._targets.values())

    async def delete_target(self, target_id: str) -> None:
        """Delete a scan target."""
        if target_id not in self._targets:
            raise TargetNotFoundError(f"Scan target not found: {target_id}")
        del self._targets[target_id]
        self._log.info("depscan.target.deleted", target_id=target_id)

    async def run_scan(self, target_id: str, scan_id: str) -> ScanResult:
        """Run a scan against a target."""
        target = self._targets.get(target_id)
        if target is None:
            raise TargetNotFoundError(f"Scan target not found: {target_id}")
        started = utc_now()
        ScanStarted(scan_id=scan_id, target_id=target_id, started_at=started)
        vulnerabilities: list[Vulnerability] = []
        for vuln in self._vulnerabilities.values():
            if vuln.target_id == target_id:
                vulnerabilities.append(vuln)
        completed = utc_now()
        delta = (completed - started).total_seconds()
        result = ScanResult(
            scan_id=scan_id,
            target_id=target_id,
            started_at=started,
            completed_at=completed,
            vulnerabilities=tuple(vulnerabilities),
            total_vulnerabilities=len(vulnerabilities),
            success=True,
        )
        self._results[scan_id] = result
        ScanCompleted(
            scan_id=scan_id,
            target_id=target_id,
            total_vulnerabilities=len(vulnerabilities),
            success=True,
            duration_seconds=round(delta, 3),
        )
        self._log.info(
            "depscan.scan.completed",
            scan_id=scan_id,
            target_id=target_id,
            vulnerabilities=len(vulnerabilities),
        )
        return result

    async def add_vulnerability(self, vulnerability: Vulnerability) -> Vulnerability:
        """Record a detected vulnerability."""
        target = self._targets.get(vulnerability.target_id)
        if target is None:
            raise TargetNotFoundError(f"Scan target not found: {vulnerability.target_id}")
        self._vulnerabilities[vulnerability.id] = vulnerability
        VulnerabilityFound(
            vulnerability_id=vulnerability.id,
            target_id=vulnerability.target_id,
            cve_id=vulnerability.cve_id,
            severity=vulnerability.severity,
            description=vulnerability.description,
        )
        self._log.info(
            "depscan.vulnerability.found",
            vuln_id=vulnerability.id,
            target_id=vulnerability.target_id,
            severity=vulnerability.severity,
        )
        return vulnerability

    async def get_vulnerability(self, vulnerability_id: str) -> Vulnerability:
        """Get a vulnerability by ID."""
        vuln = self._vulnerabilities.get(vulnerability_id)
        if vuln is None:
            raise TargetNotFoundError(f"Vulnerability not found: {vulnerability_id}")
        return vuln

    async def list_vulnerabilities(
        self,
        target_id: str | None = None,
        severity: Severity | None = None,
    ) -> list[Vulnerability]:
        """List vulnerabilities, optionally filtered."""
        vulns = list(self._vulnerabilities.values())
        if target_id is not None:
            vulns = [v for v in vulns if v.target_id == target_id]
        if severity is not None:
            vulns = [v for v in vulns if v.severity == severity]
        return vulns

    async def get_result(self, scan_id: str) -> ScanResult:
        """Get a scan result by scan ID."""
        result = self._results.get(scan_id)
        if result is None:
            raise TargetNotFoundError(f"Scan result not found: {scan_id}")
        return result

    async def list_results(self, target_id: str | None = None) -> list[ScanResult]:
        """List scan results, optionally filtered by target."""
        results = list(self._results.values())
        if target_id is not None:
            results = [r for r in results if r.target_id == target_id]
        return results

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about scans and vulnerabilities."""
        total_targets = len(self._targets)
        total_vulnerabilities = len(self._vulnerabilities)
        by_severity: dict[str, int] = {}
        for vuln in self._vulnerabilities.values():
            by_severity[vuln.severity.value] = by_severity.get(vuln.severity.value, 0) + 1
        total_scans = len(self._results)
        return {
            "total_targets": total_targets,
            "total_vulnerabilities": total_vulnerabilities,
            "by_severity": by_severity,
            "total_scans": total_scans,
        }


__all__ = ["DependencyScanner"]
