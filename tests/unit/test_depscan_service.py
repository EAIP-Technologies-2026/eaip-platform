"""Tests for DependencyScanner."""

from __future__ import annotations

import pytest

from eaip.depscan.exceptions import TargetNotFoundError
from eaip.depscan.models import ScanConfig, ScanTarget, ScanTargetType, Severity, Vulnerability
from eaip.depscan.scanner import DependencyScanner


class TestDependencyScanner:
    @pytest.fixture
    def scanner(self) -> DependencyScanner:
        return DependencyScanner()

    @pytest.fixture
    def sample_target(self) -> ScanTarget:
        return ScanTarget(id="t1", name="requests", type=ScanTargetType.LIBRARY, location="pypi")

    class TestRegisterTarget:
        async def test_registers_target(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            result = await scanner.register_target(sample_target)
            assert result.id == "t1"
            assert result.name == "requests"

        async def test_stores_target(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            stored = await scanner.get_target("t1")
            assert stored.id == "t1"

    class TestGetTarget:
        async def test_returns_target(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            result = await scanner.get_target("t1")
            assert result.name == "requests"

        async def test_raises_on_missing(self, scanner: DependencyScanner) -> None:
            with pytest.raises(TargetNotFoundError):
                await scanner.get_target("nonexistent")

    class TestDeleteTarget:
        async def test_deletes_target(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            await scanner.delete_target("t1")
            assert await scanner.list_targets() == []

        async def test_raises_on_missing(self, scanner: DependencyScanner) -> None:
            with pytest.raises(TargetNotFoundError):
                await scanner.delete_target("nonexistent")

    class TestAddVulnerability:
        async def test_adds_vulnerability(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            vuln = Vulnerability(
                id="v1", target_id="t1", cve_id="CVE-2025-0001", severity=Severity.CRITICAL
            )
            result = await scanner.add_vulnerability(vuln)
            assert result.id == "v1"

        async def test_raises_on_missing_target(self, scanner: DependencyScanner) -> None:
            vuln = Vulnerability(id="v1", target_id="nonexistent", severity=Severity.LOW)
            with pytest.raises(TargetNotFoundError):
                await scanner.add_vulnerability(vuln)

    class TestRunScan:
        async def test_runs_scan(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            result = await scanner.run_scan("t1", "sc1")
            assert result.success is True
            assert result.target_id == "t1"

        async def test_raises_on_missing_target(self, scanner: DependencyScanner) -> None:
            with pytest.raises(TargetNotFoundError):
                await scanner.run_scan("nonexistent", "sc1")

    class TestListVulnerabilities:
        async def test_filters_by_target(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            vuln = Vulnerability(id="v1", target_id="t1", severity=Severity.HIGH)
            await scanner.add_vulnerability(vuln)
            vulns = await scanner.list_vulnerabilities(target_id="t1")
            assert len(vulns) == 1

        async def test_filters_by_severity(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            v1 = Vulnerability(id="v1", target_id="t1", severity=Severity.CRITICAL)
            v2 = Vulnerability(id="v2", target_id="t1", severity=Severity.LOW)
            await scanner.add_vulnerability(v1)
            await scanner.add_vulnerability(v2)
            vulns = await scanner.list_vulnerabilities(severity=Severity.CRITICAL)
            assert len(vulns) == 1

    class TestGetResult:
        async def test_returns_result(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            await scanner.run_scan("t1", "sc1")
            result = await scanner.get_result("sc1")
            assert result.scan_id == "sc1"

    class TestGetStatistics:
        async def test_returns_stats(
            self, scanner: DependencyScanner, sample_target: ScanTarget
        ) -> None:
            await scanner.register_target(sample_target)
            stats = await scanner.get_statistics()
            assert stats["total_targets"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            svc = DependencyScanner()
            assert svc.config.max_concurrent_scans == 3

        def test_custom_config(self) -> None:
            cfg = ScanConfig(max_concurrent_scans=10)
            svc = DependencyScanner(config=cfg)
            assert svc.config.max_concurrent_scans == 10
