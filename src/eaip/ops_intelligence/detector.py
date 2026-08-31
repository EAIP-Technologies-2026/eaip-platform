"""InsightDetector — deterministic, tenant-scoped event → insights."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.ops_intelligence.models import Insight


def _tenant_of(event: dict[str, Any], default: str = "default") -> str:
    return str(event.get("tenant_id") or event.get("tenantId") or default)


class InsightDetector:
    """Deterministic detector.

    Rules (all tenant-scoped):
    - if any event has latency > 1000 -> anomaly (high severity)
    - if error count (>5) across events batch -> anomaly (critical)
    - if workforce utilization > 0.9 -> bottleneck (high)
    Events without tenant_id are treated as default tenant and filtered
    by caller; detector still tags insight with the event's tenant.
    """

    def detect(self, events: list[dict[str, Any]]) -> list[Insight]:
        if not events:
            return []
        insights: list[Insight] = []

        # Group by tenant so each insight is tenant-scoped
        by_tenant: dict[str, list[dict[str, Any]]] = {}
        for e in events:
            t = _tenant_of(e)
            by_tenant.setdefault(t, []).append(e)

        for tenant_id, tenant_events in by_tenant.items():
            # Rule 1: latency > 1000
            for ev in tenant_events:
                latency = ev.get("latency")
                if latency is None:
                    latency = ev.get("latency_ms")
                try:
                    lat_val = float(latency) if latency is not None else None
                except Exception:
                    lat_val = None
                if lat_val is not None and lat_val > 1000:
                    insights.append(
                        Insight(
                            insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                            tenant_id=tenant_id,
                            type="anomaly",
                            severity="high",
                            evidence=(dict(ev), {"rule": "latency>1000", "latency": lat_val}),
                            source="detector",
                            confidence=0.85,
                            affected_systems=tuple(
                                filter(None, [str(ev.get("system") or ev.get("service") or "unknown")])
                            ),
                            recommendation="Investigate latency spike; check downstream dependencies and autoscaling.",
                            status="open",
                        )
                    )
                    break  # one per tenant per batch for latency

            # Rule 2: error count > 5
            error_count = 0
            error_evidence: list[dict[str, Any]] = []
            for ev in tenant_events:
                is_error = False
                if ev.get("error") or ev.get("is_error"):
                    is_error = True
                lvl = str(ev.get("level") or ev.get("severity") or "").lower()
                if lvl in ("error", "critical", "fatal"):
                    is_error = True
                et = str(ev.get("event_type") or ev.get("type") or "").lower()
                if et in ("error", "failure", "exception"):
                    is_error = True
                if is_error:
                    error_count += 1
                    error_evidence.append(dict(ev))
            if error_count > 5:
                insights.append(
                    Insight(
                        insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                        tenant_id=tenant_id,
                        type="anomaly",
                        severity="critical",
                        evidence=tuple(error_evidence[:10]) + ({"rule": "error_count>5", "count": error_count},),
                        source="detector",
                        confidence=0.92,
                        affected_systems=("error_pipeline",),
                        recommendation="Error threshold exceeded; triage failing service and review recent deploys.",
                        status="open",
                    )
                )

            # Rule 3: workforce utilization > 0.9
            for ev in tenant_events:
                util = None
                # direct field
                if "workforce_utilization" in ev:
                    util = ev.get("workforce_utilization")
                elif "utilization" in ev:
                    # only if workforce context
                    if ev.get("domain") == "workforce" or ev.get("system") == "workforce" or "workforce" in str(ev.get("event_type", "")):
                        util = ev.get("utilization")
                # nested
                if util is None and isinstance(ev.get("workforce"), dict):
                    util = ev["workforce"].get("utilization")
                try:
                    util_val = float(util) if util is not None else None
                except Exception:
                    util_val = None
                if util_val is not None and util_val > 0.9:
                    insights.append(
                        Insight(
                            insight_id=f"ins-{uuid.uuid4().hex[:8]}",
                            tenant_id=tenant_id,
                            type="bottleneck",
                            severity="high",
                            evidence=(dict(ev), {"rule": "workforce_utilization>0.9", "utilization": util_val}),
                            source="detector",
                            confidence=0.8,
                            affected_systems=("workforce",),
                            recommendation="Workforce bottleneck detected; rebalance load or add capacity.",
                            status="open",
                        )
                    )
                    break

        return insights


__all__ = ["InsightDetector"]
