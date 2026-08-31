"""Tests for :mod:`eaip.healthrpt.events`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.healthrpt.events import (
    ComponentStatusChanged,
    ReportGenerated,
    SLAViolation,
)

ReportGenerated.__test__ = False
SLAViolation.__test__ = False
ComponentStatusChanged.__test__ = False


class TestHealthRptEvents:
    def test_report_generated(self) -> None:
        e = ReportGenerated(report_id="r1", overall_status="healthy", sla_achievement=99.95)
        assert e.event_type == "eaip.healthrpt.report.generated"
        assert e.report_id == "r1"
        assert e.sla_achievement == 99.95

    def test_sla_violation(self) -> None:
        e = SLAViolation(
            component_id="c1",
            component_name="API",
            sla_target=99.9,
            actual_achievement=95.0,
        )
        assert e.event_type == "eaip.healthrpt.sla.violation"
        assert e.component_id == "c1"
        assert e.actual_achievement == 95.0

    def test_component_status_changed(self) -> None:
        e = ComponentStatusChanged(
            component_id="c1",
            component_name="API",
            previous_status="healthy",
            new_status="degraded",
        )
        assert e.event_type == "eaip.healthrpt.component.status_changed"
        assert e.previous_status == "healthy"
        assert e.new_status == "degraded"


class TestEventImmutability:
    def test_report_generated_frozen(self) -> None:
        e = ReportGenerated(report_id="r1", overall_status="healthy", sla_achievement=99.0)
        with pytest.raises(ValidationError):
            e.report_id = "changed"


class TestEventOccurredAt:
    def test_has_timestamp(self) -> None:
        e = ReportGenerated(report_id="r1", overall_status="healthy", sla_achievement=99.0)
        assert e.occurred_at is not None
