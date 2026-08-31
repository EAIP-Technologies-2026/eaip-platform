"""Simulation scenarios for Apex, Nova, and Meridian enterprises."""

from __future__ import annotations

from eaip.simulation.scenarios.apex import SCENARIO as APEX_SCENARIO
from eaip.simulation.scenarios.apex import generate_payload as apex_payload
from eaip.simulation.scenarios.meridian import SCENARIO as MERIDIAN_SCENARIO
from eaip.simulation.scenarios.meridian import generate_payload as meridian_payload
from eaip.simulation.scenarios.nova import SCENARIO as NOVA_SCENARIO
from eaip.simulation.scenarios.nova import generate_payload as nova_payload

SCENARIOS: dict[str, dict] = {
    "apex": APEX_SCENARIO,
    "nova": NOVA_SCENARIO,
    "meridian": MERIDIAN_SCENARIO,
}

GENERATORS: dict[str, object] = {
    "apex": apex_payload,
    "nova": nova_payload,
    "meridian": meridian_payload,
}

__all__ = ["APEX_SCENARIO", "GENERATORS", "MERIDIAN_SCENARIO", "NOVA_SCENARIO", "SCENARIOS"]
