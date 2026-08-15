"""EAIP Conductor Phase 8 — Guided Platform Tour / Teaching Mode.

The tour is a capability of the existing Personal Assistant.  It reuses the
Conductor governance pipeline, existing voice services, and the existing tool
registry.  It does NOT create a second assistant, voice runtime, or governance
pipeline.
"""

from __future__ import annotations

from eaip.copilot.tour.models import (
    TourCommand,
    TourContext,
    TourDemoFixture,
    TourRequest,
    TourResponse,
    TourState,
    TourStep,
)
from eaip.copilot.tour.service import TourService

__all__ = [
    "TourCommand",
    "TourContext",
    "TourDemoFixture",
    "TourRequest",
    "TourResponse",
    "TourService",
    "TourState",
    "TourStep",
]
