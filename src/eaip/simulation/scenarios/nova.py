"""Nova enterprise scenario — manufacturing & operations simulation."""

from __future__ import annotations

import random
from typing import Any

SCENARIO: dict[str, Any] = {
    "id": "nova",
    "enterprise": "nova",
    "name": "Nova Manufacturing — Operations",
    "description": "Production incidents, quality alerts, maintenance, and supply-chain delays.",
    "phases": (
        "production_incident",
        "quality_alert",
        "maintenance_scheduled",
        "supply_delay",
    ),
}

_LINES = ["Line-A", "Line-B", "Line-C", "Line-D"]
_PRIORITIES = ["low", "medium", "high", "critical"]
_SEVERITIES = ["minor", "major", "critical", "blocker"]
_SUPPLIERS = ["AlloyWorks", "Precision Parts Co", "Global Components", "Apex Materials"]


def _hex(rng: random.Random, bits: int = 32) -> str:
    return format(rng.getrandbits(bits), f"0{bits // 4}x")


def generate_payload(rng: random.Random) -> dict[str, Any]:
    """Generate a realistic Nova payload picking a random phase."""
    event_type: str = rng.choice(list(SCENARIO["phases"]))  # type: ignore[arg-type]

    if event_type == "production_incident":
        payload: dict[str, Any] = {
            "incident_id": f"inc_{_hex(rng, 32)}",
            "line": rng.choice(_LINES),
            "machine_id": f"mcn_{rng.randint(1000, 9999)}",
            "severity": rng.choice(_SEVERITIES),
            "priority": rng.choice(_PRIORITIES),
            "description": rng.choice(
                ["Throughput drop detected", "Unplanned stoppage", "Sensor anomaly", "Thermal overrun"]
            ),
            "shift": rng.choice(["morning", "afternoon", "night"]),
            "operator": f"op_{rng.randint(1000, 9999)}",
        }
    elif event_type == "quality_alert":
        payload = {
            "alert_id": f"qa_{_hex(rng, 32)}",
            "line": rng.choice(_LINES),
            "batch_id": f"batch_{_hex(rng, 24)}",
            "product": rng.choice(["Widget-X", "Module-Y", "Assembly-Z", "Unit-Q"]),
            "severity": rng.choice(_SEVERITIES),
            "priority": rng.choice(_PRIORITIES),
            "metric": rng.choice(["defect_rate", "tolerance", "surface_finish", "weight"]),
            "measured_value": round(rng.uniform(0.5, 5.0), 2),
            "threshold": round(rng.uniform(0.5, 3.0), 2),
        }
    elif event_type == "maintenance_scheduled":
        payload = {
            "work_order_id": f"wo_{_hex(rng, 32)}",
            "line": rng.choice(_LINES),
            "machine_id": f"mcn_{rng.randint(1000, 9999)}",
            "maintenance_type": rng.choice(["preventive", "corrective", "predictive", "emergency"]),
            "priority": rng.choice(_PRIORITIES),
            "scheduled_for": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T08:00:00Z",
            "duration_hours": rng.randint(1, 12),
            "technician": f"tech_{rng.randint(1000, 9999)}",
        }
    else:  # supply_delay
        payload = {
            "delay_id": f"dly_{_hex(rng, 32)}",
            "supplier": rng.choice(_SUPPLIERS),
            "part_number": f"PN-{rng.randint(10000, 99999)}",
            "part_name": rng.choice(["Bearing Set", "Actuator", "Seal Kit", "Controller Board"]),
            "priority": rng.choice(_PRIORITIES),
            "delay_days": rng.randint(1, 21),
            "impact": rng.choice(["low", "moderate", "high"]),
            "purchase_order": f"PO-{rng.randint(100000, 999999)}",
        }

    return {"event_type": event_type, "payload": payload}


__all__ = ["SCENARIO", "generate_payload"]
