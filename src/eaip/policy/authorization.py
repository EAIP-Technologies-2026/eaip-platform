"""AuthorizationManager — high-level authorization facade.

Integrates the PolicyEngine with the PolicyRegistry and EventBus.
Supports capability-level authorization checks for use as middleware.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from eaip.events.event import DomainEvent
from eaip.logging.context import get_logger
from eaip.policy.context import PolicyEvaluationContext
from eaip.policy.engine import PolicyEngine
from eaip.policy.events import PolicyEvaluated, PolicyViolation
from eaip.policy.exceptions import PolicyViolationError
from eaip.policy.models import PolicyDecision, PolicyEffect

if TYPE_CHECKING:
    from eaip.events.bus import EventBus
    from eaip.policy.registry import PolicyRegistry


class AuthorizationManager:
    """High-level authorization facade.

    Combines a PolicyEngine and PolicyRegistry to answer
    authorization queries and enforce access decisions.
    """

    def __init__(
        self,
        engine: PolicyEngine,
        registry: PolicyRegistry,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the AuthorizationManager.

        Args:
            engine: The policy engine to evaluate requests.
            registry: The policy registry to load policies from.
            event_bus: Optional event bus for publishing policy events.
        """
        self._engine = engine
        self._registry = registry
        self._event_bus = event_bus
        self._log = get_logger("eaip.policy.authorization")

    def check_permission(self, context: PolicyEvaluationContext) -> PolicyDecision:
        """Evaluate whether a request is allowed (non-raising)."""
        return self._engine.evaluate(context, self._registry.enabled())

    def authorize(self, context: PolicyEvaluationContext) -> None:
        """Evaluate and enforce authorization.

        Args:
            context: The evaluation context.

        Raises:
            PolicyViolationError: If the request is denied.
        """
        decision = self.check_permission(context)
        self._publish_events(context, decision)
        if decision.effect is PolicyEffect.DENY:
            raise PolicyViolationError(
                decision.explanation,
                context={
                    "subject_id": context.subject_id,
                    "action": context.action,
                    "resource": context.resource,
                    "matched_rules": list(decision.matched_rules),
                },
            )

    def authorize_capability(
        self,
        capability_name: str,
        context: PolicyEvaluationContext,
    ) -> None:
        """Convenience method: authorize invocation of a specific capability.

        Sets the action to ``"capability:invoke"`` and the resource to the
        capability name before delegating to ``authorize``.

        Args:
            capability_name: The name of the capability being invoked.
            context: The evaluation context.

        Raises:
            PolicyViolationError: If the request is denied.
        """
        cap_context = PolicyEvaluationContext(
            subject_id=context.subject_id,
            subject_roles=context.subject_roles,
            action="capability:invoke",
            resource=capability_name,
            attributes=dict(context.attributes),
            correlation_id=context.correlation_id,
        )
        self.authorize(cap_context)

    def _publish_events(
        self,
        context: PolicyEvaluationContext,
        decision: PolicyDecision,
    ) -> None:
        if not self._event_bus:
            return

        evt = PolicyEvaluated(
            subject_id=context.subject_id,
            action=context.action,
            resource=context.resource,
            effect=decision.effect.value,
            matched_rules=decision.matched_rules,
            context_snapshot=decision.context_snapshot,
            correlation_id=context.correlation_id,
        )
        self._safe_publish(evt)

        if decision.effect is PolicyEffect.DENY:
            violation = PolicyViolation(
                subject_id=context.subject_id,
                action=context.action,
                resource=context.resource,
                matched_rules=decision.matched_rules,
                explanation=decision.explanation,
                attributes=dict(context.attributes),
                correlation_id=context.correlation_id,
            )
            self._safe_publish(violation)

    def _safe_publish(self, event: DomainEvent) -> None:
        """Publish an event to the bus, handling sync/async safely."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                _t = loop.create_task(self._event_bus.publish(event))  # type: ignore[union-attr]  # noqa: RUF006
                return
        except RuntimeError:
            pass
        asyncio.run(self._event_bus.publish(event))  # type: ignore[union-attr]


__all__ = ["AuthorizationManager"]
