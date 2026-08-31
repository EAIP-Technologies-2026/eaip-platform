"""BrainAccessManager — subject/role-based access control for brain queries."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.brain.events import BrainAccessDenied
from eaip.brain.exceptions import BrainAccessDeniedError
from eaip.brain.models import BrainQuery
from eaip.logging.context import get_logger
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.engine import PolicyEngine
from eaip.policy.models import Policy, PolicyDecision, PolicyEffect


class BrainSubject(BaseModel):
    """A subject (user or service) making a brain query."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str
    roles: tuple[str, ...] = ()
    attributes: dict[str, Any] = Field(default_factory=dict)


class BrainAccessManager:
    """Manages access control for brain queries.

    Supports enterprise-level and department-level access distinctions
    with subject/role-based policy evaluation. Integrates with the
    platform's PolicyEngine and PolicyEvaluationContext.
    """

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        policies: list[Policy] | None = None,
        event_publisher: Callable[[object], None] | None = None,
    ) -> None:
        """Initialize the BrainAccessManager.

        Args:
            policy_engine: Optional PolicyEngine instance.
            policies: Optional list of policies to evaluate.
            event_publisher: Optional callable for publishing domain events.
        """
        self._policy_engine = policy_engine or PolicyEngine()
        self._policies = policies or []
        self._event_publisher = event_publisher or (lambda _: None)
        self._log = get_logger("eaip.brain.access")

    def check_access(
        self,
        subject_id: str,
        roles: tuple[str, ...],
        brain_type: str,
        department_id: str | None = None,
    ) -> bool:
        """Check whether a subject has access to a brain.

        Args:
            subject_id: The subject identifier.
            roles: The subject's roles.
            brain_type: 'enterprise' or 'department'.
            department_id: The department ID (required for department type).

        Returns:
            True if access is granted, False otherwise.
        """
        resource = f"brain:{brain_type}"
        if department_id is not None:
            resource = f"brain:{brain_type}:{department_id}"

        context = PolicyEvaluationContext(
            subject_id=subject_id,
            subject_roles=roles,
            action="query",
            resource=resource,
            attributes={
                "brain_type": brain_type,
                "department_id": department_id or "",
            },
        )

        decision: PolicyDecision = self._policy_engine.evaluate(context, self._policies)
        return decision.effect is PolicyEffect.ALLOW

    def authorize_query(
        self,
        subject: BrainSubject,
        brain_query: BrainQuery,
        *,
        department_id: str | None = None,
    ) -> None:
        """Authorize a brain query for a subject.

        Evaluates policies and raises if access is denied. Publishes
        a BrainAccessDenied event on denial.

        Args:
            subject: The subject making the query.
            brain_query: The brain query being made.
            department_id: Optional department ID for scoped access.

        Raises:
            BrainAccessDeniedError: If access is denied.
        """
        brain_type = "department" if department_id else "enterprise"
        resource = f"brain:{brain_type}"
        if department_id is not None:
            resource = f"brain:{brain_type}:{department_id}"

        context = PolicyEvaluationContext(
            subject_id=subject.subject_id,
            subject_roles=subject.roles,
            action="query",
            resource=resource,
            attributes={
                "brain_type": brain_type,
                "department_id": department_id or "",
                "query": brain_query.query,
                "collections": brain_query.collection_names,
            },
        )

        decision: PolicyDecision = self._policy_engine.evaluate(context, self._policies)

        if decision.effect is PolicyEffect.DENY:
            self._event_publisher(
                BrainAccessDenied(
                    subject_id=subject.subject_id,
                    brain_type=brain_type,
                    department_id=department_id or "",
                    action="query",
                    reason=decision.explanation,
                )
            )
            self._log.warning(
                "access.denied",
                subject_id=subject.subject_id,
                resource=resource,
                reason=decision.explanation,
            )
            raise BrainAccessDeniedError(
                f"Access denied for {subject.subject_id} on {resource}: {decision.explanation}",
                context={
                    "subject_id": subject.subject_id,
                    "resource": resource,
                    "explanation": decision.explanation,
                },
            )

        self._log.debug(
            "access.allowed",
            subject_id=subject.subject_id,
            resource=resource,
        )


__all__ = ["BrainAccessManager", "BrainSubject"]
