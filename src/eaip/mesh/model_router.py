"""Model router — model-aware request routing with weighted distribution, failover, and health-based routing."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from eaip.logging.context import get_logger
from eaip.mesh.events import ModelRerouted, ModelRouteFailed
from eaip.mesh.exceptions import MeshError


@dataclass
class ModelEndpoint:
    model_id: str
    provider: str
    endpoint: str
    weight: int = 100
    is_active: bool = True
    latency_p50: float = 0.0
    error_rate: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingTarget:
    endpoint: ModelEndpoint
    score: float


class ModelRouter:
    def __init__(self, event_bus: Any = None) -> None:
        self._endpoints: dict[str, list[ModelEndpoint]] = {}
        self._event_bus = event_bus
        self._log = get_logger("eaip.mesh.model_router")

    def register_endpoint(self, endpoint: ModelEndpoint) -> None:
        if endpoint.model_id not in self._endpoints:
            self._endpoints[endpoint.model_id] = []
        self._endpoints[endpoint.model_id].append(endpoint)

    def unregister_endpoint(self, model_id: str, endpoint: str) -> None:
        endpoints = self._endpoints.get(model_id, [])
        self._endpoints[model_id] = [e for e in endpoints if e.endpoint != endpoint]

    def get_endpoints(self, model_id: str) -> list[ModelEndpoint]:
        return list(self._endpoints.get(model_id, []))

    def route(self, model_id: str, *, prefer_provider: str | None = None) -> ModelEndpoint:
        candidates = self._endpoints.get(model_id)
        if not candidates:
            msg = f"No endpoints registered for model '{model_id}'"
            raise MeshError(msg)

        active = [e for e in candidates if e.is_active]
        if not active:
            self._publish_failure(model_id, "all endpoints inactive")
            msg = f"All endpoints for model '{model_id}' are inactive"
            raise MeshError(msg)

        if prefer_provider:
            preferred = [e for e in active if e.provider == prefer_provider]
            if preferred:
                active = preferred

        total_weight = sum(e.weight for e in active)
        if total_weight == 0:
            selected = random.choice(active)
        else:
            r = random.uniform(0, total_weight)
            cumulative = 0.0
            selected = active[0]
            for e in active:
                cumulative += e.weight
                if r <= cumulative:
                    selected = e
                    break

        if prefer_provider and selected.provider != prefer_provider:
            self._publish_reroute(model_id, selected)
        return selected

    def route_weighted(self, model_id: str, weights: dict[str, int]) -> ModelEndpoint:
        candidates = self._endpoints.get(model_id)
        if not candidates:
            msg = f"No endpoints registered for model '{model_id}'"
            raise MeshError(msg)

        active = [e for e in candidates if e.is_active]
        if not active:
            self._publish_failure(model_id, "all endpoints inactive")
            msg = f"All endpoints for model '{model_id}' are inactive"
            raise MeshError(msg)

        scored: list[RoutingTarget] = []
        for ep in active:
            w = weights.get(ep.provider, 1)
            score = w * (1.0 - ep.error_rate) / max(ep.latency_p50, 0.001)
            scored.append(RoutingTarget(endpoint=ep, score=score))

        scored.sort(key=lambda t: t.score, reverse=True)
        return scored[0].endpoint

    def health_check(self, model_id: str) -> dict[str, Any]:
        endpoints = self._endpoints.get(model_id, [])
        return {
            "model_id": model_id,
            "total_endpoints": len(endpoints),
            "active_endpoints": sum(1 for e in endpoints if e.is_active),
            "inactive_endpoints": sum(1 for e in endpoints if not e.is_active),
            "endpoints": [
                {
                    "provider": e.provider,
                    "endpoint": e.endpoint,
                    "active": e.is_active,
                    "latency_p50": e.latency_p50,
                    "error_rate": e.error_rate,
                }
                for e in endpoints
            ],
        }

    def mark_inactive(self, model_id: str, endpoint: str) -> None:
        for e in self._endpoints.get(model_id, []):
            if e.endpoint == endpoint:
                e.is_active = False
                self._publish_failure(model_id, f"endpoint {endpoint} marked inactive")

    def mark_active(self, model_id: str, endpoint: str) -> None:
        for e in self._endpoints.get(model_id, []):
            if e.endpoint == endpoint:
                e.is_active = True

    def report_latency(self, model_id: str, endpoint: str, latency: float) -> None:
        for e in self._endpoints.get(model_id, []):
            if e.endpoint == endpoint:
                e.latency_p50 = 0.9 * e.latency_p50 + 0.1 * latency

    def report_error(self, model_id: str, endpoint: str) -> None:
        for e in self._endpoints.get(model_id, []):
            if e.endpoint == endpoint:
                e.error_rate = min(1.0, e.error_rate + 0.05)

    def _publish_reroute(self, model_id: str, endpoint: ModelEndpoint) -> None:
        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(
                    self._event_bus.publish(
                        ModelRerouted(
                            model_id=model_id,
                            provider=endpoint.provider,
                            endpoint=endpoint.endpoint,
                        )
                    )
                )
            except Exception:
                pass

    def _publish_failure(self, model_id: str, reason: str) -> None:
        if self._event_bus is not None:
            import asyncio

            try:
                asyncio.ensure_future(
                    self._event_bus.publish(
                        ModelRouteFailed(
                            model_id=model_id,
                            reason=reason,
                        )
                    )
                )
            except Exception:
                pass


__all__ = ["ModelEndpoint", "ModelRouter", "RoutingTarget"]
