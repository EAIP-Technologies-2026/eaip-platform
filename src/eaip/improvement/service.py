"""ImprovementService — lifecycle OUTCOME→EVALUATE→PROPOSE→SIMULATE→REVIEW→DEPLOY→MEASURE."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from eaip.improvement.models import ImprovementProposal
from eaip.shared.time import utc_now


def _stable_risk(problem: dict[str, Any]) -> str:
    h = hashlib.sha256(str(sorted(problem.items())).encode()).hexdigest()
    n = int(h[:2], 16) % 3
    return ("low", "medium", "high")[n]


class ImprovementService:
    """Tenant-isolated improvement lifecycle service.

    Keyed by ``{tenant_id}:{proposal_id}``.
    """

    def __init__(self) -> None:
        self._store: dict[str, ImprovementProposal] = {}

    def _key(self, tenant_id: str, proposal_id: str) -> str:
        return f"{tenant_id}:{proposal_id}"

    # ── propose ─────────────────────────────────────────────────

    def propose(
        self,
        tenant: str,
        source: str,
        problem: dict[str, Any],
        root_cause: str = "",
        proposed_change: str = "",
        expected_benefit: str = "",
        evidence: list[dict[str, Any]] | None = None,
    ) -> ImprovementProposal:
        proposal_id = f"imp-{uuid.uuid4().hex[:8]}"
        prob = dict(problem) if problem else {}
        rc = root_cause or str(prob.get("root_cause") or prob.get("cause") or "under investigation")
        pc = proposed_change or str(prob.get("proposed_change") or prob.get("change") or prob.get("title") or "proposed fix")
        eb = expected_benefit or str(prob.get("expected_benefit") or prob.get("benefit") or "reduced risk / improved throughput")
        risk = str(prob.get("risk") or _stable_risk(prob))
        if risk not in ("low", "medium", "high", "critical"):
            risk = "low"
        prop = ImprovementProposal(
            proposal_id=proposal_id,
            tenant_id=tenant,
            source=source or "manual",
            problem=prob,
            root_cause=rc,
            proposed_change=pc,
            expected_benefit=eb,
            risk=risk,
            evidence=tuple(evidence or prob.get("evidence") or []),
            simulation={},
            approval={},
            implementation={},
            measured_outcome={},
            status="proposed",
        )
        # lifecycle: simulate step (deterministic placeholder)
        sim = self._simulate_for(prop)
        prop = prop.model_copy(update={"simulation": sim, "status": "simulated"})
        self._store[self._key(tenant, proposal_id)] = prop
        return prop

    def _simulate_for(self, prop: ImprovementProposal) -> dict[str, Any]:
        seed = f"{prop.tenant_id}:{prop.proposal_id}:{prop.problem}"
        h = hashlib.sha256(seed.encode()).hexdigest()
        n = int(h[:8], 16)
        frac = n / 0xFFFFFFFF
        return {
            "simulated_cost": int(5000 + frac * 100_000),
            "simulated_time_days": int(2 + frac * 30),
            "simulated_risk": round(0.1 + frac * 0.6, 2),
            "confidence": round(0.6 + frac * 0.3, 2),
            "note": "deterministic simulated outcome",
            "at": utc_now().isoformat(),
        }

    # ── review ──────────────────────────────────────────────────

    def review(self, proposal_id: str, tenant: str, approved: bool) -> ImprovementProposal | None:
        cur = self._store.get(self._key(tenant, proposal_id))
        if cur is None:
            return None
        if cur.status not in ("simulated", "proposed", "review"):
            # allow re-review from simulated/review
            pass
        new_status = "approved" if approved else "rejected"
        updated = cur.model_copy(
            update={
                "approval": {"approved": approved, "at": utc_now().isoformat()},
                "status": new_status,
                "updated_at": utc_now(),
            }
        )
        self._store[self._key(tenant, proposal_id)] = updated
        return updated

    # ── apply / deploy ──────────────────────────────────────────

    def apply(self, proposal_id: str, tenant: str) -> ImprovementProposal | None:
        cur = self._store.get(self._key(tenant, proposal_id))
        if cur is None:
            return None
        if cur.status != "approved":
            raise ValueError(f"proposal {proposal_id!r} must be approved before deploy (current: {cur.status})")
        updated = cur.model_copy(
            update={
                "implementation": {"deployed_at": utc_now().isoformat(), "by": tenant},
                "status": "deployed",
                "updated_at": utc_now(),
            }
        )
        self._store[self._key(tenant, proposal_id)] = updated
        return updated

    # ── measure ─────────────────────────────────────────────────

    def measure(self, proposal_id: str, tenant: str, outcome: dict[str, Any]) -> ImprovementProposal | None:
        cur = self._store.get(self._key(tenant, proposal_id))
        if cur is None:
            return None
        if cur.status != "deployed":
            raise ValueError(f"proposal {proposal_id!r} must be deployed before measure (current: {cur.status})")
        updated = cur.model_copy(
            update={
                "measured_outcome": dict(outcome) if outcome else {},
                "status": "measured",
                "updated_at": utc_now(),
            }
        )
        self._store[self._key(tenant, proposal_id)] = updated
        return updated

    # ── accessors ───────────────────────────────────────────────

    def get(self, proposal_id: str, tenant: str) -> ImprovementProposal | None:
        return self._store.get(self._key(tenant, proposal_id))

    def list_for_tenant(self, tenant: str) -> list[ImprovementProposal]:
        prefix = f"{tenant}:"
        return [v for k, v in self._store.items() if k.startswith(prefix)]


__all__ = ["ImprovementService"]
