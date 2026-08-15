"""Bounded, explainable anomaly detection for EAIP Conductor (Phase 3).

Evaluates System Twin state and domain events to produce proactive nudges.
Every anomaly contains strict OBSERVED, INFERRED, RECOMMENDED fields and enforces throttling.
"""

from __future__ import annotations

import time

from pydantic import BaseModel

from eaip.copilot.twin import SystemTwinState


class AnomalyNudge(BaseModel):
    """Proactive anomaly nudge containing explainable diagnostic fields."""

    id: str
    severity: str = "WARNING"  # CRITICAL, WARNING, INFO
    title: str
    observed: str
    inferred: str
    recommended: str
    component: str
    timestamp: str
    dismissed: bool = False


class AnomalyDetector:
    """Deterministic anomaly detector with deduplication and cooldown throttling."""

    def __init__(self, cooldown_seconds: float = 300.0) -> None:
        """Initialize the detector with a per-key emission cooldown.

        Args:
            cooldown_seconds: Minimum seconds between emissions of the same key.
        """
        self._cooldown = cooldown_seconds
        self._last_emitted: dict[str, float] = {}
        self._dismissed_ids: set[str] = set()

    def analyze(self, state: SystemTwinState) -> list[AnomalyNudge]:
        """Analyze twin state and return active, non-cooled-down anomalies."""
        now = time.time()
        anomalies: list[AnomalyNudge] = []

        # Rule 1: Health Degradation
        if state.health != "healthy":
            key = f"health_degraded_{state.health}"
            if self._should_emit(key, now):
                anomalies.append(
                    AnomalyNudge(
                        id=key,
                        severity="CRITICAL" if state.health == "unhealthy" else "WARNING",
                        title=f"System Health {state.health.capitalize()}",
                        observed=(
                            f"Platform health status changed to '{state.health}': "
                            f"{state.health_message}"
                        ),
                        inferred=(
                            "Subsystem check detected component failure or "
                            "degradation."
                        ),
                        recommended=(
                            "Inspect platform health diagnostics and verify "
                            "subservice availability."
                        ),
                        component="HealthSubsystem",
                        timestamp=state.last_updated,
                    )
                )

        # Rule 2: Component Failures
        for fail in state.recent_failures:
            comp = fail.get("component", "system")
            key = f"failure_{comp}"
            if self._should_emit(key, now):
                anomalies.append(
                    AnomalyNudge(
                        id=key,
                        severity="WARNING",
                        title=f"Operational Warning in {comp}",
                        observed=(
                            f"Component '{comp}' reported error: {fail.get('error')}"
                        ),
                        inferred=(
                            f"Repeated error signals in {comp} may indicate "
                            "service degradation."
                        ),
                        recommended=(
                            f"Check logs for {comp} and restart service if "
                            "necessary."
                        ),
                        component=comp,
                        timestamp=fail.get("timestamp", state.last_updated),
                    )
                )

        return [a for a in anomalies if a.id not in self._dismissed_ids]

    def dismiss(self, anomaly_id: str) -> None:
        """Dismiss an active anomaly nudge."""
        self._dismissed_ids.add(anomaly_id)

    def _should_emit(self, key: str, now: float) -> bool:
        last = self._last_emitted.get(key, 0.0)
        if now - last >= self._cooldown:
            self._last_emitted[key] = now
            return True
        return False
