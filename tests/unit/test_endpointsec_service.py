"""Tests for EndpointSecurityScanner."""

from __future__ import annotations

import pytest

from eaip.endpointsec.exceptions import EndpointNotFoundError
from eaip.endpointsec.models import (
    Endpoint,
    EndpointStatus,
    ScanConfig,
    ScanFinding,
    ScanProfile,
    Severity,
)
from eaip.endpointsec.scanner import EndpointSecurityScanner


class TestEndpointSecurityScanner:
    @pytest.fixture
    def scanner(self) -> EndpointSecurityScanner:
        return EndpointSecurityScanner()

    @pytest.fixture
    def sample_endpoint(self) -> Endpoint:
        return Endpoint(id="ep1", name="api-gw", host="10.0.0.1", port=443)

    class TestRegisterEndpoint:
        async def test_registers_endpoint(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            result = await scanner.register_endpoint(sample_endpoint)
            assert result.id == "ep1"
            assert result.name == "api-gw"

        async def test_stores_endpoint(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            stored = await scanner.get_endpoint("ep1")
            assert stored.host == "10.0.0.1"

    class TestGetEndpoint:
        async def test_returns_endpoint(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            result = await scanner.get_endpoint("ep1")
            assert result.name == "api-gw"

        async def test_raises_on_missing(self, scanner: EndpointSecurityScanner) -> None:
            with pytest.raises(EndpointNotFoundError):
                await scanner.get_endpoint("nonexistent")

    class TestDeleteEndpoint:
        async def test_deletes_endpoint(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            await scanner.delete_endpoint("ep1")
            assert await scanner.list_endpoints() == []

        async def test_raises_on_missing(self, scanner: EndpointSecurityScanner) -> None:
            with pytest.raises(EndpointNotFoundError):
                await scanner.delete_endpoint("nonexistent")

    class TestUpdateStatus:
        async def test_updates_status(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            result = await scanner.update_status("ep1", EndpointStatus.ONLINE)
            assert result.status == EndpointStatus.ONLINE

    class TestReportFinding:
        async def test_reports_finding(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            finding = ScanFinding(id="f1", endpoint_id="ep1", severity=Severity.CRITICAL)
            result = await scanner.report_finding(finding)
            assert result.id == "f1"

        async def test_raises_on_missing_endpoint(self, scanner: EndpointSecurityScanner) -> None:
            finding = ScanFinding(id="f1", endpoint_id="nonexistent", severity=Severity.LOW)
            with pytest.raises(EndpointNotFoundError):
                await scanner.report_finding(finding)

    class TestResolveFinding:
        async def test_resolves_finding(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            finding = ScanFinding(id="f1", endpoint_id="ep1", severity=Severity.HIGH)
            await scanner.report_finding(finding)
            resolved = await scanner.resolve_finding("f1")
            assert resolved.resolved_at is not None

    class TestRunScan:
        async def test_runs_scan(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            findings = await scanner.run_scan("ep1", "sc1")
            assert isinstance(findings, list)

        async def test_raises_on_missing_endpoint(self, scanner: EndpointSecurityScanner) -> None:
            with pytest.raises(EndpointNotFoundError):
                await scanner.run_scan("nonexistent", "sc1")

    class TestAddProfile:
        async def test_adds_profile(self, scanner: EndpointSecurityScanner) -> None:
            profile = ScanProfile(id="p1", name="full-scan", checks=("port", "tls"))
            result = await scanner.add_profile(profile)
            assert result.id == "p1"

        async def test_gets_profile(self, scanner: EndpointSecurityScanner) -> None:
            profile = ScanProfile(id="p1", name="quick")
            await scanner.add_profile(profile)
            result = await scanner.get_profile("p1")
            assert result.name == "quick"

    class TestListFindings:
        async def test_filters_by_endpoint(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            f1 = ScanFinding(id="f1", endpoint_id="ep1", severity=Severity.HIGH)
            f2 = ScanFinding(id="f2", endpoint_id="ep1", severity=Severity.LOW)
            await scanner.report_finding(f1)
            await scanner.report_finding(f2)
            findings = await scanner.list_findings(endpoint_id="ep1")
            assert len(findings) == 2

        async def test_filters_by_severity(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            f1 = ScanFinding(id="f1", endpoint_id="ep1", severity=Severity.CRITICAL)
            f2 = ScanFinding(id="f2", endpoint_id="ep1", severity=Severity.LOW)
            await scanner.report_finding(f1)
            await scanner.report_finding(f2)
            findings = await scanner.list_findings(severity=Severity.CRITICAL)
            assert len(findings) == 1

    class TestGetStatistics:
        async def test_returns_stats(
            self, scanner: EndpointSecurityScanner, sample_endpoint: Endpoint
        ) -> None:
            await scanner.register_endpoint(sample_endpoint)
            stats = await scanner.get_statistics()
            assert stats["total_endpoints"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = EndpointSecurityScanner()
            assert svc.config.max_concurrent_scans == 5

        def test_custom_config(self) -> None:
            cfg = ScanConfig(max_concurrent_scans=10)
            svc = EndpointSecurityScanner(config=cfg)
            assert svc.config.max_concurrent_scans == 10
