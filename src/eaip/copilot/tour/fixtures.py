"""Tour fixture service — create, track, and clean up safe demo fixtures.

Every temporary object is tagged with ``tour_session_id`` and carries an
explicit cleanup lifecycle.  Fixtures CANNOT access real objects and are
never used to bypass governance.
"""

from __future__ import annotations

import uuid
from typing import Any

from eaip.admin.audit import AuditLogger
from eaip.admin.models import AuditEntry, AuditOutcome
from eaip.copilot.tour.models import TourDemoFixture
from eaip.logging.context import get_logger
from eaip.shared.identifiers import CorrelationId


class TourFixtureService:
    """Manage safe demo fixtures for an active tour session."""

    def __init__(self, audit: AuditLogger) -> None:
        """Initialize the fixture service with an audit logger."""
        self._audit = audit
        self._log = get_logger("eaip.copilot.tour.fixtures")
        self._fixtures: dict[str, list[TourDemoFixture]] = {}

    def create_fixture(
        self,
        tour_session_id: str,
        fixture_type: str,
        name: str,
        data: dict[str, Any] | None = None,
    ) -> TourDemoFixture:
        """Create a temporary demo fixture tagged with the tour session.

        Args:
            tour_session_id: The active tour session identifier.
            fixture_type: The type of fixture (e.g. 'agent', 'workflow').
            name: Human-readable fixture name.
            data: Optional fixture data.

        Returns:
            The created fixture.
        """
        fixture = TourDemoFixture(
            id=f"tour-fixture-{uuid.uuid4().hex[:12]}",
            tour_session_id=tour_session_id,
            fixture_type=fixture_type,
            name=name,
            data=data or {},
        )
        self._fixtures.setdefault(tour_session_id, []).append(fixture)
        self._audit.log(
            AuditEntry(
                id=f"audit-tour-fixture-{uuid.uuid4().hex[:12]}",
                actor_id="tour_system",
                action="tour.fixture.created",
                resource_type="tour_fixture",
                resource_id=fixture.id,
                outcome=AuditOutcome.SUCCESS,
                details={
                    "tour_session_id": tour_session_id,
                    "fixture_type": fixture_type,
                    "name": name,
                },
                correlation_id=str(CorrelationId.new()),
            )
        )
        self._log.info(
            "tour.fixture.created",
            fixture_id=fixture.id,
            tour_session_id=tour_session_id,
            fixture_type=fixture_type,
        )
        return fixture

    def list_fixtures(self, tour_session_id: str) -> list[TourDemoFixture]:
        """List all fixtures for a tour session."""
        return list(self._fixtures.get(tour_session_id, []))

    async def cleanup_session(self, tour_session_id: str) -> list[TourDemoFixture]:
        """Clean up all fixtures for a completed or cancelled tour session.

        Returns:
            List of fixtures that were cleaned up.

        Raises:
            RuntimeError: If any fixture cleanup fails.
        """
        fixtures = self._fixtures.get(tour_session_id, [])
        cleaned: list[TourDemoFixture] = []
        errors: list[str] = []

        for fixture in fixtures:
            try:
                cleaned_fixture = fixture.model_copy(update={"cleaned_up": True})
                cleaned.append(cleaned_fixture)
                self._audit.log(
                    AuditEntry(
                        id=f"audit-tour-cleanup-{uuid.uuid4().hex[:12]}",
                        actor_id="tour_system",
                        action="tour.fixture.cleaned_up",
                        resource_type="tour_fixture",
                        resource_id=fixture.id,
                        outcome=AuditOutcome.SUCCESS,
                        details={
                            "tour_session_id": tour_session_id,
                            "fixture_type": fixture.fixture_type,
                        },
                        correlation_id=str(CorrelationId.new()),
                    )
                )
            except Exception as exc:
                error_msg = f"Failed to clean up fixture {fixture.id}: {exc!r}"
                errors.append(error_msg)
                self._log.error(
                    "tour.fixture.cleanup_failed",
                    fixture_id=fixture.id,
                    error=str(exc),
                )
                self._audit.log(
                    AuditEntry(
                        id=(f"audit-tour-cleanup-fail-{uuid.uuid4().hex[:12]}"),
                        actor_id="tour_system",
                        action="tour.fixture.cleanup_failed",
                        resource_type="tour_fixture",
                        resource_id=fixture.id,
                        outcome=AuditOutcome.FAILURE,
                        details={
                            "tour_session_id": tour_session_id,
                            "error": repr(exc),
                        },
                        correlation_id=str(CorrelationId.new()),
                    )
                )

        if tour_session_id in self._fixtures:
            del self._fixtures[tour_session_id]

        if errors:
            raise RuntimeError(
                f"Tour fixture cleanup had {len(errors)} error(s): " + "; ".join(errors)
            )

        self._log.info(
            "tour.fixtures.cleaned_up",
            tour_session_id=tour_session_id,
            count=len(cleaned),
        )
        return cleaned

    def fixture_count(self, tour_session_id: str) -> int:
        """Return the number of active fixtures for a session."""
        return len(self._fixtures.get(tour_session_id, []))


__all__ = ["TourFixtureService"]
