"""Apex enterprise scenario — client lifecycle simulation."""

from __future__ import annotations

import random
from typing import Any

SCENARIO: dict[str, Any] = {
    "id": "apex",
    "enterprise": "apex",
    "name": "Apex Advisory — Client Lifecycle",
    "description": "Professional services client onboarding, engagement, and delivery tracking.",
    "phases": (
        "client_onboarding",
        "engagement_created",
        "proposal_sent",
        "delivery_tracking",
    ),
}

_CLIENT_NAMES = [
    "Acme Corp",
    "Globex Industries",
    "Initech LLC",
    "Umbrella Holdings",
    "Wayne Enterprises",
    "Stark Dynamics",
    "Wonka Industries",
    "Gekko Capital",
]

_ENGAGEMENT_TYPES = ["advisory", "audit", "consulting", "implementation", "assessment"]
_PRIORITIES = ["low", "medium", "high", "critical"]
_PROPOSAL_STATUSES = ["draft", "sent", "under_review", "accepted", "rejected"]
_DELIVERY_STATUSES = ["on_track", "at_risk", "delayed", "completed"]


def _hex(rng: random.Random, bits: int = 32) -> str:
    return format(rng.getrandbits(bits), f"0{bits // 4}x")


def generate_payload(rng: random.Random) -> dict[str, Any]:
    """Generate a realistic Apex payload picking a random phase.

    Args:
        rng: Deterministic random source seeded by SimulationEngine.

    Returns:
        Dict with event_type and payload keys.
    """
    event_type: str = rng.choice(list(SCENARIO["phases"]))  # type: ignore[arg-type]

    if event_type == "client_onboarding":
        payload: dict[str, Any] = {
            "client_id": f"cli_{_hex(rng, 32)}",
            "client_name": rng.choice(_CLIENT_NAMES),
            "industry": rng.choice(["finance", "healthcare", "technology", "manufacturing", "retail"]),
            "onboarding_stage": rng.choice(["intake", "kyc", "contracts", "kickoff"]),
            "owner": f"user_{rng.randint(1000, 9999)}",
            "priority": rng.choice(_PRIORITIES),
            "estimated_value": rng.randint(25_000, 500_000),
        }
    elif event_type == "engagement_created":
        payload = {
            "engagement_id": f"eng_{_hex(rng, 32)}",
            "client_id": f"cli_{_hex(rng, 32)}",
            "client_name": rng.choice(_CLIENT_NAMES),
            "engagement_type": rng.choice(_ENGAGEMENT_TYPES),
            "title": f"{rng.choice(['Digital', 'Strategy', 'Risk', 'Ops'])} Engagement {rng.randint(100, 999)}",
            "priority": rng.choice(_PRIORITIES),
            "budget": rng.randint(50_000, 1_000_000),
            "owner": f"user_{rng.randint(1000, 9999)}",
        }
    elif event_type == "proposal_sent":
        payload = {
            "proposal_id": f"prop_{_hex(rng, 32)}",
            "engagement_id": f"eng_{_hex(rng, 32)}",
            "client_name": rng.choice(_CLIENT_NAMES),
            "title": f"Proposal {rng.randint(1000, 9999)} — {rng.choice(_CLIENT_NAMES)}",
            "status": rng.choice(_PROPOSAL_STATUSES),
            "value": rng.randint(20_000, 800_000),
            "priority": rng.choice(_PRIORITIES),
            "owner": f"user_{rng.randint(1000, 9999)}",
        }
    else:  # delivery_tracking
        payload = {
            "delivery_id": f"del_{_hex(rng, 32)}",
            "engagement_id": f"eng_{_hex(rng, 32)}",
            "milestone": rng.choice(["Design", "Build", "Test", "Launch", "Hypercare"]),
            "status": rng.choice(_DELIVERY_STATUSES),
            "progress_pct": rng.randint(0, 100),
            "priority": rng.choice(_PRIORITIES),
            "owner": f"user_{rng.randint(1000, 9999)}",
            "eta_days": rng.randint(1, 60),
        }

    return {"event_type": event_type, "payload": payload}


__all__ = ["SCENARIO", "generate_payload"]
