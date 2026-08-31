"""Meridian enterprise scenario — healthcare compliance & care simulation."""

from __future__ import annotations

import random
from typing import Any

SCENARIO: dict[str, Any] = {
    "id": "meridian",
    "enterprise": "meridian",
    "name": "Meridian Health — Compliance & Care",
    "description": "Compliance events, audits, escalations, and care-plan updates.",
    "phases": (
        "compliance_event",
        "audit_required",
        "escalation",
        "care_plan_update",
    ),
}

_PRIORITIES = ["low", "medium", "high", "critical"]
_COMPLIANCE_TYPES = ["HIPAA", "SOX", "GDPR", "FDA", "Joint Commission"]
_AUDIT_TYPES = ["internal", "external", "regulatory", "surprise"]
_ESCALATION_REASONS = ["clinical_risk", "staffing", "equipment", "patient_complaint"]
_CARE_ACTIONS = ["medication_change", "therapy_added", "discharge_planning", "follow_up_scheduled"]


def _hex(rng: random.Random, bits: int = 32) -> str:
    return format(rng.getrandbits(bits), f"0{bits // 4}x")


def generate_payload(rng: random.Random) -> dict[str, Any]:
    """Generate a realistic Meridian payload picking a random phase."""
    event_type: str = rng.choice(list(SCENARIO["phases"]))  # type: ignore[arg-type]

    if event_type == "compliance_event":
        payload: dict[str, Any] = {
            "event_id": f"cev_{_hex(rng, 32)}",
            "compliance_type": rng.choice(_COMPLIANCE_TYPES),
            "finding": rng.choice(
                ["Documentation gap", "Access review overdue", "Training incomplete", "Policy violation"]
            ),
            "facility": rng.choice(["North Wing", "South Wing", "ICU", "Outpatient"]),
            "priority": rng.choice(_PRIORITIES),
            "assignee": f"user_{rng.randint(1000, 9999)}",
            "due_days": rng.randint(1, 30),
        }
    elif event_type == "audit_required":
        payload = {
            "audit_id": f"aud_{_hex(rng, 32)}",
            "audit_type": rng.choice(_AUDIT_TYPES),
            "compliance_type": rng.choice(_COMPLIANCE_TYPES),
            "scope": rng.choice(["unit", "department", "facility", "enterprise"]),
            "priority": rng.choice(_PRIORITIES),
            "scheduled_for": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T09:00:00Z",
            "auditor": f"auditor_{rng.randint(1000, 9999)}",
            "facility": rng.choice(["North Wing", "South Wing", "ICU", "Outpatient"]),
        }
    elif event_type == "escalation":
        payload = {
            "escalation_id": f"esc_{_hex(rng, 32)}",
            "reason": rng.choice(_ESCALATION_REASONS),
            "priority": rng.choice(_PRIORITIES),
            "severity": rng.choice(["minor", "major", "critical"]),
            "unit": rng.choice(["ER", "ICU", "Pediatrics", "Oncology"]),
            "reported_by": f"user_{rng.randint(1000, 9999)}",
            "patient_id": f"pat_{_hex(rng, 24)}",
            "requires_followup": rng.choice([True, False]),
        }
    else:  # care_plan_update
        payload = {
            "plan_id": f"plan_{_hex(rng, 32)}",
            "patient_id": f"pat_{_hex(rng, 24)}",
            "patient_name": rng.choice(["Patient A", "Patient B", "Patient C", "Patient D"]),
            "action": rng.choice(_CARE_ACTIONS),
            "priority": rng.choice(_PRIORITIES),
            "clinician": f"dr_{rng.randint(1000, 9999)}",
            "unit": rng.choice(["ER", "ICU", "Pediatrics", "Oncology"]),
            "effective_date": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            "notes": rng.choice(["Per attending review", "Family requested", "Protocol update", "Lab results reviewed"]),
        }

    return {"event_type": event_type, "payload": payload}


__all__ = ["SCENARIO", "generate_payload"]
