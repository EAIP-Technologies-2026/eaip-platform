"""Compliance framework — regulations, controls, scanning, and scoring."""

from __future__ import annotations

from typing import Any

from eaip.compliance.events import (
    ComplianceScanCompleted,
    ComplianceScanStarted,
    ControlStatusChanged,
)
from eaip.compliance.exceptions import RegulationNotFoundError
from eaip.compliance.models import ComplianceReport, Control, Regulation
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class RegulationMapper:
    """Maps controls to regulations and checks coverage."""

    def __init__(self) -> None:
        """Initialize the regulation mapper."""
        self._log = get_logger("eaip.compliance.mapper")
        self._regulation_controls: dict[str, dict[str, Control]] = {}

    def register_control(self, control: Control) -> None:
        """Register a control with the mapper."""
        self._regulation_controls.setdefault(control.regulation_id, {})[control.control_id] = (
            control
        )

    def get_controls_for_regulation(self, regulation_id: str) -> tuple[Control, ...]:
        """Get all controls for a regulation."""
        controls = self._regulation_controls.get(regulation_id, {})
        return tuple(controls.values())

    def get_coverage(self, regulation_id: str) -> dict[str, Any]:
        """Get coverage statistics for a regulation."""
        controls = self.get_controls_for_regulation(regulation_id)
        total = len(controls)
        if total == 0:
            return {"total": 0, "covered": 0, "coverage": 0.0}
        covered = sum(1 for c in controls if c.status != "unknown")
        return {
            "total": total,
            "covered": covered,
            "coverage": round(covered / total * 100, 2),
        }

    def find_gaps(self, regulation: Regulation) -> list[str]:
        """Find gaps in control coverage for a regulation."""
        registered = set(self._regulation_controls.get(regulation.regulation_id, {}).keys())
        required = set(regulation.required_controls)
        return sorted(required - registered)

    def clear(self) -> None:
        """Clear all registered controls."""
        self._regulation_controls.clear()


class ComplianceFramework:
    """Central compliance framework — register regulations, controls, run scans, and compute scores."""

    def __init__(self) -> None:
        """Initialize the compliance framework."""
        self._log = get_logger("eaip.compliance.framework")
        self._regulations: dict[str, Regulation] = {}
        self._mapper = RegulationMapper()
        self._scan_history: list[ComplianceReport] = []

    def register_regulation(self, regulation: Regulation) -> None:
        """Register a regulation."""
        self._regulations[regulation.regulation_id] = regulation

    def register_control(self, control: Control) -> None:
        """Register a control."""
        self._mapper.register_control(control)

    def get_regulation(self, regulation_id: str) -> Regulation:
        """Get a regulation by ID."""
        regulation = self._regulations.get(regulation_id)
        if regulation is None:
            raise RegulationNotFoundError(f"Regulation {regulation_id!r} not found")
        return regulation

    def list_regulations(self) -> tuple[Regulation, ...]:
        """List all registered regulations."""
        return tuple(self._regulations.values())

    def list_controls(self, regulation_id: str | None = None) -> tuple[Control, ...]:
        """List all controls, optionally filtered by regulation."""
        if regulation_id is not None:
            return self._mapper.get_controls_for_regulation(regulation_id)
        all_controls: list[Control] = []
        for reg_id in self._mapper._regulation_controls:
            all_controls.extend(self._mapper._regulation_controls[reg_id].values())
        return tuple(all_controls)

    def get_mapper(self) -> RegulationMapper:
        """Return the regulation mapper."""
        return self._mapper

    def _compute_score(self, controls: tuple[Control, ...]) -> float:
        total = len(controls)
        if total == 0:
            return 100.0
        compliant = sum(1 for c in controls if c.status == "compliant")
        sum(1 for c in controls if c.status == "non_compliant")
        applicable = total - sum(1 for c in controls if c.status == "not_applicable")
        if applicable == 0:
            return 100.0
        return round(compliant / applicable * 100, 2)

    def _determine_status(self, score: float) -> str:
        if score >= 90.0:  # noqa: PLR2004
            return "compliant"
        if score >= 50.0:  # noqa: PLR2004
            return "partially_compliant"
        return "non_compliant"

    async def run_scan(
        self,
        regulation_id: str,
        scan_id: str,
        event_bus: Any = None,
    ) -> ComplianceReport:
        """Run a compliance scan for a regulation."""
        self.get_regulation(regulation_id)
        if event_bus is not None:
            await event_bus.publish(
                ComplianceScanStarted(regulation_id=regulation_id, scan_id=scan_id)
            )

        controls = self._mapper.get_controls_for_regulation(regulation_id)
        score = self._compute_score(controls)
        status = self._determine_status(score)
        total = len(controls)
        compliant = sum(1 for c in controls if c.status == "compliant")
        non_compliant = sum(1 for c in controls if c.status == "non_compliant")

        report = ComplianceReport(
            report_id=f"scan-{scan_id}",
            generated_at=utc_now(),
            regulation_id=regulation_id,
            overall_status=status,
            controls=controls,
            total_controls=total,
            compliant_count=compliant,
            non_compliant_count=non_compliant,
            score=score,
        )
        self._scan_history.append(report)

        if event_bus is not None:
            await event_bus.publish(
                ComplianceScanCompleted(
                    regulation_id=regulation_id,
                    scan_id=scan_id,
                    score=score,
                    status=status,
                )
            )

        return report

    async def update_control_status(
        self,
        control_id: str,
        new_status: str,
        event_bus: Any = None,
    ) -> Control:
        """Update the status of a control."""
        for controls in self._mapper._regulation_controls.values():
            if control_id in controls:
                control = controls[control_id]
                previous_status = control.status
                if previous_status == new_status:
                    return control
                updated = Control(
                    control_id=control.control_id,
                    regulation_id=control.regulation_id,
                    category=control.category,
                    description=control.description,
                    severity=control.severity,
                    status=new_status,
                )
                controls[control_id] = updated
                if event_bus is not None:
                    await event_bus.publish(
                        ControlStatusChanged(
                            control_id=control_id,
                            previous_status=previous_status,
                            new_status=new_status,
                        )
                    )
                return updated
        raise RegulationNotFoundError(f"Control {control_id!r} not found")

    def get_scan_history(self) -> tuple[ComplianceReport, ...]:
        """Return the scan history."""
        return tuple(self._scan_history)

    def clear(self) -> None:
        """Clear all data."""
        self._regulations.clear()
        self._mapper.clear()
        self._scan_history.clear()
