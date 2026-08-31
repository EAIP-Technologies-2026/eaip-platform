"""Cost optimizer — generate and manage optimization recommendations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from eaip.cost.exceptions import RecommendationNotFoundError
from eaip.cost.models import (
    Category,
    CostRecord,
    OptimizationRecommendation,
    RecommendationEffort,
    RecommendationRisk,
    RecommendationStatus,
    RecommendationType,
)
from eaip.cost.tracker import CostTracker


class CostOptimizer:
    """Generates and manages cost optimization recommendations."""

    def __init__(self, tracker: CostTracker) -> None:
        self._tracker = tracker
        self._recommendations: dict[str, OptimizationRecommendation] = {}
        self._event_callback: Callable[..., Any] | None = None
        self._rec_counter: int = 0

    def set_event_callback(self, callback: Callable[..., Any]) -> None:
        self._event_callback = callback

    async def _emit(self, event: Any) -> None:
        if self._event_callback is not None:
            await self._event_callback(event)

    async def generate_recommendations(self) -> list[OptimizationRecommendation]:
        generated: list[OptimizationRecommendation] = []
        records = await self._tracker.query_costs()

        # group by resource_type + resource_id and classify
        groups: dict[tuple[str | None, str | None], list[CostRecord]] = defaultdict(list)
        for r in records:
            groups[(r.resource_type, r.resource_id)].append(r)

        for (res_type, res_id), items in groups.items():
            if res_type is None or res_id is None:
                continue
            total_cost = sum(item.amount for item in items)
            if total_cost <= 0:
                continue

            # rightsize recommendation for compute resources with high cost
            if "compute" in res_type.lower() or any(
                item.category is Category.COMPUTE for item in items
            ):
                if total_cost > 100:
                    self._rec_counter += 1
                    rec = OptimizationRecommendation(
                        id=f"rec-{self._rec_counter}",
                        type=RecommendationType.RIGHTSIZE,
                        resource_type=res_type,
                        resource_id=res_id,
                        current_cost=total_cost,
                        estimated_savings=total_cost * 0.3,
                        effort=RecommendationEffort.MEDIUM,
                        risk=RecommendationRisk.LOW,
                        description=f"Rightsize {res_type} {res_id}",
                        rationale=f"Resource costs ${total_cost:.2f}; estimated 30% savings via rightsizing.",
                    )
                    self._recommendations[rec.id] = rec
                    generated.append(rec)
                    if self._event_callback is not None:
                        from eaip.cost.events import RecommendationGenerated

                        await self._event_callback(
                            RecommendationGenerated(
                                recommendation_id=rec.id,
                                type=rec.type.value,
                                resource_type=res_type,
                                resource_id=res_id,
                                estimated_savings=rec.estimated_savings,
                            )
                        )

            # stop recommendation for low-usage resources
            if total_cost < 10 and len(items) <= 2:
                self._rec_counter += 1
                rec = OptimizationRecommendation(
                    id=f"rec-{self._rec_counter}",
                    type=RecommendationType.STOP,
                    resource_type=res_type,
                    resource_id=res_id,
                    current_cost=total_cost,
                    estimated_savings=total_cost,
                    effort=RecommendationEffort.LOW,
                    risk=RecommendationRisk.LOW,
                    description=f"Stop low-usage {res_type} {res_id}",
                    rationale=f"Resource costs only ${total_cost:.2f}; stopping saves 100%.",
                )
                self._recommendations[rec.id] = rec
                generated.append(rec)
                if self._event_callback is not None:
                    from eaip.cost.events import RecommendationGenerated

                    await self._event_callback(
                        RecommendationGenerated(
                            recommendation_id=rec.id,
                            type=rec.type.value,
                            resource_type=res_type,
                            resource_id=res_id,
                            estimated_savings=rec.estimated_savings,
                        )
                    )

        return generated

    async def get_recommendations(
        self,
        resource_type: str | None = None,
        status: str | None = None,
    ) -> list[OptimizationRecommendation]:
        results = list(self._recommendations.values())
        if resource_type is not None:
            results = [r for r in results if r.resource_type == resource_type]
        if status is not None:
            results = [r for r in results if r.status.value == status]
        return results

    async def apply_recommendation(self, recommendation_id: str) -> OptimizationRecommendation:
        if recommendation_id not in self._recommendations:
            raise RecommendationNotFoundError(f"Recommendation {recommendation_id} not found")
        rec = self._recommendations[recommendation_id]
        updated = OptimizationRecommendation(
            id=rec.id,
            type=rec.type,
            resource_type=rec.resource_type,
            resource_id=rec.resource_id,
            current_cost=rec.current_cost,
            estimated_savings=rec.estimated_savings,
            effort=rec.effort,
            risk=rec.risk,
            description=rec.description,
            rationale=rec.rationale,
            status=RecommendationStatus.APPLIED,
            created_at=rec.created_at,
            metadata=rec.metadata,
        )
        self._recommendations[recommendation_id] = updated
        if self._event_callback is not None:
            from eaip.cost.events import RecommendationApplied

            await self._event_callback(
                RecommendationApplied(
                    recommendation_id=recommendation_id,
                    type=rec.type.value,
                    resource_id=rec.resource_id,
                )
            )
        return updated

    async def dismiss_recommendation(self, recommendation_id: str) -> OptimizationRecommendation:
        if recommendation_id not in self._recommendations:
            raise RecommendationNotFoundError(f"Recommendation {recommendation_id} not found")
        rec = self._recommendations[recommendation_id]
        updated = OptimizationRecommendation(
            id=rec.id,
            type=rec.type,
            resource_type=rec.resource_type,
            resource_id=rec.resource_id,
            current_cost=rec.current_cost,
            estimated_savings=rec.estimated_savings,
            effort=rec.effort,
            risk=rec.risk,
            description=rec.description,
            rationale=rec.rationale,
            status=RecommendationStatus.DISMISSED,
            created_at=rec.created_at,
            metadata=rec.metadata,
        )
        self._recommendations[recommendation_id] = updated
        return updated

    async def get_potential_savings(self) -> float:
        total = 0.0
        for rec in self._recommendations.values():
            if rec.status is RecommendationStatus.OPEN:
                total += rec.estimated_savings
        return total
