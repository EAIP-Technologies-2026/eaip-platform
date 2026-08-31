from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eaip.compliance.exceptions import RegulationNotFoundError
from eaip.compliance.framework import ComplianceFramework
from eaip.compliance.models import Control, Regulation


class TestComplianceFramework:
    @pytest.fixture
    def framework(self) -> ComplianceFramework:
        fw = ComplianceFramework()
        fw.register_regulation(
            Regulation(
                regulation_id="gdpr",
                name="GDPR",
                description="General Data Protection Regulation",
                version="1.0",
                required_controls=("c1", "c2"),
            )
        )
        fw.register_regulation(
            Regulation(
                regulation_id="hipaa",
                name="HIPAA",
                description="Health Insurance Portability and Accountability Act",
                version="2.0",
            )
        )
        fw.register_control(
            Control(
                control_id="c1",
                regulation_id="gdpr",
                category="access",
                description="Access control",
                severity="high",
                status="compliant",
            )
        )
        fw.register_control(
            Control(
                control_id="c2",
                regulation_id="gdpr",
                category="encryption",
                description="Encryption at rest",
                severity="critical",
                status="non_compliant",
            )
        )
        return fw

    def test_register_regulation(self, framework: ComplianceFramework) -> None:
        regs = framework.list_regulations()
        assert len(regs) == 2

    def test_register_control(self, framework: ComplianceFramework) -> None:
        controls = framework.list_controls("gdpr")
        assert len(controls) == 2

    def test_list_regulations(self, framework: ComplianceFramework) -> None:
        regs = framework.list_regulations()
        assert regs[0].regulation_id == "gdpr"
        assert regs[1].regulation_id == "hipaa"

    def test_list_controls_all(self, framework: ComplianceFramework) -> None:
        controls = framework.list_controls()
        assert len(controls) == 2

    def test_list_controls_by_regulation(self, framework: ComplianceFramework) -> None:
        controls = framework.list_controls("gdpr")
        assert all(c.regulation_id == "gdpr" for c in controls)
        assert len(controls) == 2

    def test_list_controls_empty(self, framework: ComplianceFramework) -> None:
        controls = framework.list_controls("hipaa")
        assert controls == ()

    def test_get_regulation_found(self, framework: ComplianceFramework) -> None:
        reg = framework.get_regulation("gdpr")
        assert reg.name == "GDPR"

    def test_get_regulation_not_found(self, framework: ComplianceFramework) -> None:
        with pytest.raises(RegulationNotFoundError):
            framework.get_regulation("nonexistent")

    @pytest.mark.asyncio
    async def test_run_scan(self, framework: ComplianceFramework) -> None:
        report = await framework.run_scan("gdpr", "scan-001")
        assert report.regulation_id == "gdpr"
        assert report.total_controls == 2
        assert report.compliant_count == 1
        assert report.non_compliant_count == 1
        assert report.score == 50.0
        assert report.overall_status == "partially_compliant"

    @pytest.mark.asyncio
    async def test_run_scan_with_event_bus(self, framework: ComplianceFramework) -> None:
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()
        await framework.run_scan("gdpr", "scan-002", event_bus=event_bus)
        assert event_bus.publish.call_count == 2

    @pytest.mark.asyncio
    async def test_update_control_status(self, framework: ComplianceFramework) -> None:
        updated = await framework.update_control_status("c1", "non_compliant")
        assert updated.status == "non_compliant"

    @pytest.mark.asyncio
    async def test_update_control_status_same(self, framework: ComplianceFramework) -> None:
        original = framework.list_controls("gdpr")[0]
        result = await framework.update_control_status("c1", "compliant")
        assert result is original

    @pytest.mark.asyncio
    async def test_update_control_status_not_found(self, framework: ComplianceFramework) -> None:
        with pytest.raises(RegulationNotFoundError):
            await framework.update_control_status("nonexistent", "compliant")

    @pytest.mark.asyncio
    async def test_update_control_status_with_event_bus(
        self, framework: ComplianceFramework
    ) -> None:
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()
        await framework.update_control_status("c1", "non_compliant", event_bus=event_bus)
        event_bus.publish.assert_called_once()

    def test_get_scan_history_empty(self, framework: ComplianceFramework) -> None:
        assert framework.get_scan_history() == ()

    @pytest.mark.asyncio
    async def test_get_scan_history(self, framework: ComplianceFramework) -> None:
        await framework.run_scan("gdpr", "scan-001")
        await framework.run_scan("gdpr", "scan-002")
        assert len(framework.get_scan_history()) == 2

    def test_clear(self, framework: ComplianceFramework) -> None:
        framework.clear()
        assert framework.list_regulations() == ()
        assert framework.list_controls() == ()
        assert framework.get_scan_history() == ()
