"""SimulationEngine — deterministic enterprise event generation."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from eaip.logging.context import get_logger
from eaip.shared.time import utc_now
from eaip.simulation.models import EnterpriseState, SimulationEvent


def _hex(rng: random.Random, bits: int = 48) -> str:
    return format(rng.getrandbits(bits), f"0{bits // 4}x")

_ENTERPRISES = ("apex", "nova", "meridian")

_SCENARIO_PHASES: dict[str, tuple[str, ...]] = {
    "apex": ("client_onboarding", "engagement_created", "proposal_sent", "delivery_tracking"),
    "nova": ("production_incident", "quality_alert", "maintenance_scheduled", "supply_delay"),
    "meridian": ("compliance_event", "audit_required", "escalation", "care_plan_update"),
}

# Pools for realistic payloads
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
_LINES = ["Line-A", "Line-B", "Line-C", "Line-D"]
_SEVERITIES = ["minor", "major", "critical", "blocker"]
_SUPPLIERS = ["AlloyWorks", "Precision Parts Co", "Global Components", "Apex Materials"]
_COMPLIANCE_TYPES = ["HIPAA", "SOX", "GDPR", "FDA", "Joint Commission"]
_AUDIT_TYPES = ["internal", "external", "regulatory", "surprise"]
_ESCALATION_REASONS = ["clinical_risk", "staffing", "equipment", "patient_complaint"]
_CARE_ACTIONS = ["medication_change", "therapy_added", "discharge_planning", "follow_up_scheduled"]

log = get_logger("eaip.simulation.engine")


class SimulationEngine:
    """Deterministic multi-tenant enterprise simulation engine.

    Generates realistic enterprise events for Apex (professional services),
    Nova (manufacturing), and Meridian (healthcare). All randomness is
    derived from a seeded ``random.Random`` instance so that runs are
    reproducible.

    Works in-memory when DB / event bus / knowledge graph are unavailable
    and degrades gracefully.
    """

    def __init__(
        self,
        event_bus: Any | None = None,
        knowledge_graph: Any | None = None,
        seed: int = 42,
    ) -> None:
        self._event_bus = event_bus
        self._kg = knowledge_graph
        self._seed = seed
        self._rng = random.Random(seed)
        self._events: list[SimulationEvent] = []
        self._states: dict[str, EnterpriseState] = {
            "apex": EnterpriseState(enterprise="apex", workload=0.62, utilization=0.58, active_tasks=4, alerts=1),
            "nova": EnterpriseState(enterprise="nova", workload=0.71, utilization=0.68, active_tasks=6, alerts=2),
            "meridian": EnterpriseState(enterprise="meridian", workload=0.55, utilization=0.61, active_tasks=3, alerts=1),
        }
        self._kernel: Any | None = None
        self._tick_handle: Any | None = None
        self._tick_count: int = 0
        self._log = get_logger("eaip.simulation.engine")

    # ── core generation ─────────────────────────────────────────────

    def generate_event(
        self,
        enterprise: str,
        event_type: str,
        tenant_id: str = "default",
    ) -> SimulationEvent:
        """Create a single deterministic simulation event.

        Args:
            enterprise: One of apex | nova | meridian.
            event_type: Phase name for the enterprise.
            tenant_id: Optional tenant scoping (defaults to "default").

        Returns:
            A frozen SimulationEvent with realistic payload.
        """
        if enterprise not in _SCENARIO_PHASES:
            raise ValueError(f"Unknown enterprise {enterprise!r}; expected one of {_ENTERPRISES}")
        if event_type not in _SCENARIO_PHASES[enterprise]:
            raise ValueError(f"Unknown event_type {event_type!r} for enterprise {enterprise!r}")

        payload = self._build_payload(enterprise, event_type)
        event = SimulationEvent(
            id=f"evt_{_hex(self._rng, 48)}",
            tenant_id=tenant_id,
            enterprise=enterprise,
            event_type=event_type,
            payload=payload,
            created_at=utc_now(),
        )
        self._events.append(event)
        # best-effort side effects (never fail the caller)
        self._update_state_for_event(enterprise, payload)
        return event

    def _build_payload(self, enterprise: str, event_type: str) -> dict[str, Any]:
        rng = self._rng
        # Each branch produces ids, names, and priorities
        if enterprise == "apex":
            if event_type == "client_onboarding":
                return {
                    "client_id": f"cli_{_hex(rng, 32)}",
                    "client_name": rng.choice(_CLIENT_NAMES),
                    "industry": rng.choice(["finance", "healthcare", "technology", "manufacturing", "retail"]),
                    "onboarding_stage": rng.choice(["intake", "kyc", "contracts", "kickoff"]),
                    "owner": f"user_{rng.randint(1000, 9999)}",
                    "priority": rng.choice(_PRIORITIES),
                    "estimated_value": rng.randint(25_000, 500_000),
                }
            if event_type == "engagement_created":
                return {
                    "engagement_id": f"eng_{_hex(rng, 32)}",
                    "client_id": f"cli_{_hex(rng, 32)}",
                    "client_name": rng.choice(_CLIENT_NAMES),
                    "engagement_type": rng.choice(_ENGAGEMENT_TYPES),
                    "title": f"{rng.choice(['Digital', 'Strategy', 'Risk', 'Ops'])} Engagement {rng.randint(100, 999)}",
                    "priority": rng.choice(_PRIORITIES),
                    "budget": rng.randint(50_000, 1_000_000),
                    "owner": f"user_{rng.randint(1000, 9999)}",
                }
            if event_type == "proposal_sent":
                return {
                    "proposal_id": f"prop_{_hex(rng, 32)}",
                    "engagement_id": f"eng_{_hex(rng, 32)}",
                    "client_name": rng.choice(_CLIENT_NAMES),
                    "title": f"Proposal {rng.randint(1000, 9999)} — {rng.choice(_CLIENT_NAMES)}",
                    "status": rng.choice(_PROPOSAL_STATUSES),
                    "value": rng.randint(20_000, 800_000),
                    "priority": rng.choice(_PRIORITIES),
                    "owner": f"user_{rng.randint(1000, 9999)}",
                }
            # delivery_tracking
            return {
                "delivery_id": f"del_{_hex(rng, 32)}",
                "engagement_id": f"eng_{_hex(rng, 32)}",
                "milestone": rng.choice(["Design", "Build", "Test", "Launch", "Hypercare"]),
                "status": rng.choice(_DELIVERY_STATUSES),
                "progress_pct": rng.randint(0, 100),
                "priority": rng.choice(_PRIORITIES),
                "owner": f"user_{rng.randint(1000, 9999)}",
                "eta_days": rng.randint(1, 60),
            }

        if enterprise == "nova":
            if event_type == "production_incident":
                return {
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
            if event_type == "quality_alert":
                return {
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
            if event_type == "maintenance_scheduled":
                return {
                    "work_order_id": f"wo_{_hex(rng, 32)}",
                    "line": rng.choice(_LINES),
                    "machine_id": f"mcn_{rng.randint(1000, 9999)}",
                    "maintenance_type": rng.choice(["preventive", "corrective", "predictive", "emergency"]),
                    "priority": rng.choice(_PRIORITIES),
                    "scheduled_for": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T08:00:00Z",
                    "duration_hours": rng.randint(1, 12),
                    "technician": f"tech_{rng.randint(1000, 9999)}",
                }
            # supply_delay
            return {
                "delay_id": f"dly_{_hex(rng, 32)}",
                "supplier": rng.choice(_SUPPLIERS),
                "part_number": f"PN-{rng.randint(10000, 99999)}",
                "part_name": rng.choice(["Bearing Set", "Actuator", "Seal Kit", "Controller Board"]),
                "priority": rng.choice(_PRIORITIES),
                "delay_days": rng.randint(1, 21),
                "impact": rng.choice(["low", "moderate", "high"]),
                "purchase_order": f"PO-{rng.randint(100000, 999999)}",
            }

        # meridian
        if event_type == "compliance_event":
            return {
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
        if event_type == "audit_required":
            return {
                "audit_id": f"aud_{_hex(rng, 32)}",
                "audit_type": rng.choice(_AUDIT_TYPES),
                "compliance_type": rng.choice(_COMPLIANCE_TYPES),
                "scope": rng.choice(["unit", "department", "facility", "enterprise"]),
                "priority": rng.choice(_PRIORITIES),
                "scheduled_for": f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}T09:00:00Z",
                "auditor": f"auditor_{rng.randint(1000, 9999)}",
                "facility": rng.choice(["North Wing", "South Wing", "ICU", "Outpatient"]),
            }
        if event_type == "escalation":
            return {
                "escalation_id": f"esc_{_hex(rng, 32)}",
                "reason": rng.choice(_ESCALATION_REASONS),
                "priority": rng.choice(_PRIORITIES),
                "severity": rng.choice(["minor", "major", "critical"]),
                "unit": rng.choice(["ER", "ICU", "Pediatrics", "Oncology"]),
                "reported_by": f"user_{rng.randint(1000, 9999)}",
                "patient_id": f"pat_{_hex(rng, 24)}",
                "requires_followup": rng.choice([True, False]),
            }
        # care_plan_update
        return {
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

    def _update_state_for_event(self, enterprise: str, payload: dict[str, Any]) -> None:
        cur = self._states.get(enterprise)
        if cur is None:
            return
        # nudge workload/utilization
        delta_w = self._rng.uniform(-0.05, 0.08)
        delta_u = self._rng.uniform(-0.04, 0.06)
        workload = min(1.0, max(0.05, cur.workload + delta_w))
        utilization = min(1.0, max(0.05, cur.utilization + delta_u))
        active = max(0, cur.active_tasks + self._rng.randint(-1, 2))
        # alerts bump on high/critical priority
        alerts = cur.alerts
        prio = str(payload.get("priority", "")).lower()
        sev = str(payload.get("severity", "")).lower()
        if prio in ("high", "critical") or sev in ("critical", "blocker"):
            if self._rng.random() < 0.65:
                alerts += 1
        # occasional alert decay
        if self._rng.random() < 0.25 and alerts > 0:
            alerts -= 1
        self._states[enterprise] = EnterpriseState(
            enterprise=enterprise,
            workload=round(workload, 3),
            utilization=round(utilization, 3),
            active_tasks=active,
            alerts=alerts,
        )

    def get_enterprise_state(self, enterprise: str) -> EnterpriseState:
        """Return current workload snapshot for *enterprise*."""
        if enterprise not in _SCENARIO_PHASES:
            raise ValueError(f"Unknown enterprise {enterprise!r}")
        state = self._states.get(enterprise)
        if state is not None:
            return state
        # fallback (should not happen)
        return EnterpriseState(enterprise=enterprise, workload=0.5, utilization=0.5, active_tasks=0, alerts=0)

    def tick(self) -> list[SimulationEvent]:
        """Generate 1-3 deterministic events for this tick."""
        count = self._rng.randint(1, 3)
        events: list[SimulationEvent] = []
        for _ in range(count):
            enterprise: str = self._rng.choice(list(_ENTERPRISES))  # type: ignore[assignment]
            phases = _SCENARIO_PHASES[enterprise]
            event_type: str = self._rng.choice(list(phases))  # type: ignore[assignment]
            # enterprise enterprises use default tenant for determinism
            tenant_id = "default"
            try:
                evt = self.generate_event(enterprise, event_type, tenant_id=tenant_id)
            except Exception as exc:  # pragma: no cover - defensive
                self._log.warning("simulation.tick.generate_failed", enterprise=enterprise, error=repr(exc))
                continue
            events.append(evt)
        self._tick_count += 1
        # fire-and-forget side effects (DB/KG/bus) — failures are logged, not raised
        self._try_persist_events(events)
        return events

    def _try_persist_events(self, events: list[SimulationEvent]) -> None:
        # Knowledge graph enrichment (best-effort)
        if self._kg is not None:
            for evt in events:
                try:
                    # schedule async add if loop is running; otherwise skip
                    loop = None
                    with __import__("contextlib").suppress(RuntimeError):
                        loop = asyncio.get_running_loop()
                    if loop and loop.is_running():
                        # fire and forget — kg add_entity is async
                        from eaip.kgraph.models import Entity as KGEntity

                        entity = KGEntity(
                            id=evt.id,
                            type=f"simulation_event:{evt.enterprise}:{evt.event_type}",
                            name=f"{evt.enterprise}:{evt.event_type}:{evt.id[:8]}",
                            description=f"Simulation event {evt.event_type} for {evt.enterprise}",
                            properties=dict(evt.payload),
                            source="simulation",
                            confidence=1.0,
                            metadata={"enterprise": evt.enterprise, "tenant_id": evt.tenant_id},
                            tags=(evt.enterprise, evt.event_type),
                        )
                        # schedule without awaiting in sync tick
                        asyncio.create_task(self._kg.add_entity(entity))  # type: ignore[attr-defined]
                except Exception as exc:  # pragma: no cover
                    self._log.warning("simulation.kgraph_failed", error=repr(exc))
        # Event bus publish (best-effort, handle sync or async bus)
        if self._event_bus is not None:
            for evt in events:
                try:
                    # Try to publish as domain event wrapper if bus expects DomainEvent
                    # Fall back to publishing the SimulationEvent directly.
                    maybe_coro = None
                    # Prefer generic publish; let bus decide matching
                    if hasattr(self._event_bus, "publish"):
                        result = self._event_bus.publish(evt)  # type: ignore[operator]
                        if asyncio.iscoroutine(result) or hasattr(result, "__await__"):
                            try:
                                loop2 = asyncio.get_running_loop()
                                if loop2.is_running():
                                    asyncio.create_task(result)  # type: ignore[arg-type]
                            except RuntimeError:
                                pass
                except Exception as exc:  # pragma: no cover
                    self._log.warning("simulation.bus_publish_failed", error=repr(exc))
        # DB persistence is intentionally omitted here (handled by API layer);
        # if a DB pool is available elsewhere it will be used. We keep
        # in-memory list always.

    # ── scheduler integration ───────────────────────────────────────

    async def _scheduled_tick(self) -> None:
        """Async wrapper registered with RuntimeKernel Scheduler."""
        try:
            self.tick()
        except Exception as exc:  # pragma: no cover
            self._log.error("simulation.scheduled_tick_failed", error=repr(exc))

    def start(self, kernel: Any) -> Any | None:
        """Register a recurring tick every 30s on *kernel.scheduler*.

        Args:
            kernel: RuntimeKernel (or any object exposing ``scheduler.every``).

        Returns:
            The TaskHandle for the scheduled job, or None if kernel has no scheduler.
        """
        self._kernel = kernel
        scheduler = getattr(kernel, "scheduler", None)
        if scheduler is None:
            self._log.warning("simulation.start.no_scheduler", kernel_type=type(kernel).__name__)
            return None
        try:
            handle = scheduler.every("simulation.tick", 30.0, self._scheduled_tick)
            self._tick_handle = handle
            self._log.info("simulation.started", interval=30.0, seed=self._seed)
            return handle
        except Exception as exc:  # pragma: no cover
            self._log.error("simulation.start_failed", error=repr(exc))
            return None

    def stop(self) -> None:
        """Cancel the scheduled tick, if any."""
        if self._tick_handle is not None and self._kernel is not None:
            scheduler = getattr(self._kernel, "scheduler", None)
            if scheduler is not None:
                try:
                    # Scheduler.cancel expects handle id
                    handle_id = getattr(self._tick_handle, "id", None) or str(self._tick_handle)
                    scheduler.cancel(handle_id)
                except Exception as exc:  # pragma: no cover
                    self._log.warning("simulation.stop.cancel_failed", error=repr(exc))
            self._tick_handle = None
        self._kernel = None
        self._log.info("simulation.stopped")

    # ── helpers for inspection ──────────────────────────────────────

    @property
    def events(self) -> list[SimulationEvent]:
        return list(self._events)

    @property
    def tick_count(self) -> int:
        return self._tick_count


__all__ = ["SimulationEngine"]
