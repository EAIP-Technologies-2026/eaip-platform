"""EndpointSecurityScanner — scan endpoints and report findings."""

from __future__ import annotations

from eaip.endpointsec.events import (
    EndpointRegistered,
    FindingReported,
    FindingResolved,
    ScanCompleted,
)
from eaip.endpointsec.exceptions import EndpointNotFoundError
from eaip.endpointsec.models import (
    Endpoint,
    EndpointStatus,
    ScanConfig,
    ScanFinding,
    ScanProfile,
    Severity,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class EndpointSecurityScanner:
    """Central service for scanning endpoints and tracking security findings."""

    def __init__(self, config: ScanConfig | None = None) -> None:
        self._config = config or ScanConfig()
        self._endpoints: dict[str, Endpoint] = {}
        self._findings: dict[str, ScanFinding] = {}
        self._profiles: dict[str, ScanProfile] = {}
        self._log = get_logger("eaip.endpointsec.service")

    @property
    def config(self) -> ScanConfig:
        return self._config

    async def register_endpoint(self, endpoint: Endpoint) -> Endpoint:
        """Register a new endpoint for scanning."""
        self._endpoints[endpoint.id] = endpoint
        EndpointRegistered(
            endpoint_id=endpoint.id,
            name=endpoint.name,
            host=endpoint.host,
            port=endpoint.port,
            tags=endpoint.tags,
        )
        self._log.info(
            "endpointsec.endpoint.registered", endpoint_id=endpoint.id, name=endpoint.name
        )
        return endpoint

    async def get_endpoint(self, endpoint_id: str) -> Endpoint:
        """Get an endpoint by ID."""
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint is None:
            raise EndpointNotFoundError(f"Endpoint not found: {endpoint_id}")
        return endpoint

    async def list_endpoints(self) -> list[Endpoint]:
        """List all registered endpoints."""
        return list(self._endpoints.values())

    async def delete_endpoint(self, endpoint_id: str) -> None:
        """Delete a registered endpoint."""
        if endpoint_id not in self._endpoints:
            raise EndpointNotFoundError(f"Endpoint not found: {endpoint_id}")
        del self._endpoints[endpoint_id]
        self._log.info("endpointsec.endpoint.deleted", endpoint_id=endpoint_id)

    async def update_status(self, endpoint_id: str, status: EndpointStatus) -> Endpoint:
        """Update the status of an endpoint."""
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint is None:
            raise EndpointNotFoundError(f"Endpoint not found: {endpoint_id}")
        updated = endpoint.model_copy(update={"status": status, "last_seen": utc_now()})
        self._endpoints[endpoint_id] = updated
        self._log.info("endpointsec.endpoint.status", endpoint_id=endpoint_id, status=status.value)
        return updated

    async def add_profile(self, profile: ScanProfile) -> ScanProfile:
        """Register a scan profile."""
        self._profiles[profile.id] = profile
        return profile

    async def get_profile(self, profile_id: str) -> ScanProfile:
        """Get a scan profile by ID."""
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise EndpointNotFoundError(f"Scan profile not found: {profile_id}")
        return profile

    async def run_scan(self, endpoint_id: str, scan_id: str) -> list[ScanFinding]:
        """Run a scan against an endpoint."""
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint is None:
            raise EndpointNotFoundError(f"Endpoint not found: {endpoint_id}")
        started = utc_now()
        endpoint_findings = [f for f in self._findings.values() if f.endpoint_id == endpoint_id]
        completed = utc_now()
        delta = (completed - started).total_seconds()
        critical_count = sum(1 for f in endpoint_findings if f.severity == Severity.CRITICAL)
        ScanCompleted(
            endpoint_id=endpoint_id,
            scan_id=scan_id,
            total_findings=len(endpoint_findings),
            critical_count=critical_count,
            success=True,
            duration_seconds=round(delta, 3),
        )
        await self.update_status(endpoint_id, EndpointStatus.ONLINE)
        self._log.info(
            "endpointsec.scan.completed",
            scan_id=scan_id,
            endpoint_id=endpoint_id,
            findings=len(endpoint_findings),
        )
        return endpoint_findings

    async def report_finding(self, finding: ScanFinding) -> ScanFinding:
        """Report a new security finding."""
        endpoint = self._endpoints.get(finding.endpoint_id)
        if endpoint is None:
            raise EndpointNotFoundError(f"Endpoint not found: {finding.endpoint_id}")
        self._findings[finding.id] = finding
        FindingReported(
            finding_id=finding.id,
            endpoint_id=finding.endpoint_id,
            severity=finding.severity,
            cve_id=finding.cve_id,
            description=finding.description,
        )
        self._log.info(
            "endpointsec.finding.reported",
            finding_id=finding.id,
            endpoint_id=finding.endpoint_id,
            severity=finding.severity.value,
        )
        return finding

    async def resolve_finding(self, finding_id: str) -> ScanFinding:
        """Mark a finding as resolved."""
        finding = self._findings.get(finding_id)
        if finding is None:
            raise EndpointNotFoundError(f"Finding not found: {finding_id}")
        resolved = finding.model_copy(update={"resolved_at": utc_now()})
        self._findings[finding_id] = resolved
        FindingResolved(
            finding_id=finding_id,
            endpoint_id=finding.endpoint_id,
            severity=finding.severity,
        )
        self._log.info("endpointsec.finding.resolved", finding_id=finding_id)
        return resolved

    async def get_finding(self, finding_id: str) -> ScanFinding:
        """Get a finding by ID."""
        finding = self._findings.get(finding_id)
        if finding is None:
            raise EndpointNotFoundError(f"Finding not found: {finding_id}")
        return finding

    async def list_findings(
        self, endpoint_id: str | None = None, severity: Severity | None = None
    ) -> list[ScanFinding]:
        """List findings, optionally filtered."""
        findings = list(self._findings.values())
        if endpoint_id is not None:
            findings = [f for f in findings if f.endpoint_id == endpoint_id]
        if severity is not None:
            findings = [f for f in findings if f.severity == severity]
        return findings

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about endpoints and findings."""
        total_endpoints = len(self._endpoints)
        total_findings = len(self._findings)
        by_severity: dict[str, int] = {}
        for f in self._findings.values():
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1
        unresolved = sum(1 for f in self._findings.values() if f.resolved_at is None)
        return {
            "total_endpoints": total_endpoints,
            "total_findings": total_findings,
            "by_severity": by_severity,
            "unresolved": unresolved,
        }


__all__ = ["EndpointSecurityScanner"]
