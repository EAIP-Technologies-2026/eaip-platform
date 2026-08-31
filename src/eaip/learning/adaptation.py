"""AdaptationEngine — generate governed adaptation proposals from lessons."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.learning.events import AdaptationProposed
from eaip.learning.models import AdaptationProposal, AdaptationTarget, LearningStatus, RiskLevel
from eaip.learning.persistence import LearningStore
from eaip.logging.context import get_logger


class AdaptationEngine:
    """Generates adaptation proposals from validated lessons.

    All proposals go through governance checks. High-risk changes
    require explicit approval before activation.
    """

    def __init__(
        self,
        store: LearningStore,
        event_publisher: object | None = None,
    ) -> None:
        self._store = store
        self._publish = event_publisher or (lambda _: None)
        self._log = get_logger("eaip.learning.adaptation")

    def _create_proposal(
        self,
        tenant_id: str,
        lesson_id: str,
        target_type: AdaptationTarget,
        target_id: str,
        proposed_change: dict[str, Any],
        risk_level: RiskLevel,
    ) -> AdaptationProposal:
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} not found")
        adapt_id = f"adapt-{uuid.uuid4().hex[:10]}"
        proposal = AdaptationProposal(
            id=adapt_id,
            tenant_id=tenant_id,
            lesson_id=lesson_id,
            target_type=target_type,
            target_id=target_id,
            proposed_change=proposed_change,
            risk_level=risk_level,
            status=LearningStatus.PROPOSED,
        )
        self._store.put_adaptation(proposal)
        self._publish(AdaptationProposed(
            adaptation_id=adapt_id,
            lesson_id=lesson_id,
            target_type=target_type.value,
            risk_level=risk_level.value,
            tenant_id=tenant_id,
        ))
        self._log.info("adaptation.proposed", adaptation_id=adapt_id, target=target_type.value)
        return proposal

    def propose_workflow_improvement(
        self,
        tenant_id: str,
        lesson_id: str,
        workflow_id: str,
    ) -> AdaptationProposal:
        """Propose a workflow improvement based on a lesson."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        change = {"type": "workflow_improvement", "lesson_title": lesson.title if lesson else ""}
        return self._create_proposal(
            tenant_id, lesson_id, AdaptationTarget.WORKFLOW,
            workflow_id, change, RiskLevel.MEDIUM,
        )

    def propose_methodology_update(
        self,
        tenant_id: str,
        lesson_id: str,
        methodology_id: str,
    ) -> AdaptationProposal:
        """Propose a methodology update based on a lesson."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        change = {"type": "methodology_update", "lesson_title": lesson.title if lesson else ""}
        return self._create_proposal(
            tenant_id, lesson_id, AdaptationTarget.METHODOLOGY,
            methodology_id, change, RiskLevel.HIGH,
        )

    def propose_policy_recommendation(
        self,
        tenant_id: str,
        lesson_id: str,
    ) -> AdaptationProposal:
        """Propose a policy recommendation based on a lesson."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        change = {"type": "policy_recommendation", "lesson_title": lesson.title if lesson else ""}
        return self._create_proposal(
            tenant_id, lesson_id, AdaptationTarget.POLICY,
            "", change, RiskLevel.HIGH,
        )

    def propose_agent_config_change(
        self,
        tenant_id: str,
        lesson_id: str,
        agent_id: str,
    ) -> AdaptationProposal:
        """Propose an agent configuration change based on a lesson."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        change = {"type": "agent_config_change", "lesson_title": lesson.title if lesson else ""}
        return self._create_proposal(
            tenant_id, lesson_id, AdaptationTarget.AGENT_CONFIG,
            agent_id, change, RiskLevel.MEDIUM,
        )

    def propose_model_routing_change(
        self,
        tenant_id: str,
        lesson_id: str,
    ) -> AdaptationProposal:
        """Propose a model routing change based on a lesson."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        change = {"type": "model_routing_change", "lesson_title": lesson.title if lesson else ""}
        return self._create_proposal(
            tenant_id, lesson_id, AdaptationTarget.MODEL_ROUTING,
            "", change, RiskLevel.LOW,
        )

    def propose_knowledge_update(
        self,
        tenant_id: str,
        lesson_id: str,
    ) -> AdaptationProposal:
        """Propose a knowledge base update based on a lesson."""
        lesson = self._store.get_lesson(tenant_id, lesson_id)
        change = {"type": "knowledge_update", "lesson_title": lesson.title if lesson else ""}
        return self._create_proposal(
            tenant_id, lesson_id, AdaptationTarget.KNOWLEDGE,
            "", change, RiskLevel.LOW,
        )


__all__ = ["AdaptationEngine"]
