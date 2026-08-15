"""TourService — governs the guided platform tour lifecycle.

The tour is a capability of the existing Personal Assistant / Conductor.
It reuses the existing governance pipeline, voice services (on the frontend),
and tool registry.  It does NOT create a parallel assistant or governance path.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from eaip.admin.audit import AuditLogger
from eaip.admin.models import AuditEntry, AuditOutcome
from eaip.copilot.governance import GovernancePolicy
from eaip.copilot.memory import GovernedMemoryService
from eaip.copilot.tour.fixtures import TourFixtureService
from eaip.copilot.tour.models import (
    TourCommand,
    TourContext,
    TourRequest,
    TourResponse,
    TourState,
    TourStep,
)
from eaip.copilot.tour.steps import (
    get_dynamic_tour_steps,
    get_step_by_id,
    get_tour_steps,
)
from eaip.logging.context import get_logger
from eaip.memory.models import MemoryDomain
from eaip.shared.identifiers import CorrelationId
from eaip.shared.time import utc_now

# Valid state transitions for the tour state machine.
_TRANSITIONS: dict[TourState, frozenset[TourState]] = {
    TourState.IDLE: frozenset({TourState.INTRO, TourState.CANCELLED}),
    TourState.INTRO: frozenset(
        {
            TourState.NAVIGATING,
            TourState.PAUSED,
            TourState.CANCELLED,
            TourState.COMPLETED,
        }
    ),
    TourState.NAVIGATING: frozenset(
        {
            TourState.EXPLAINING,
            TourState.PAUSED,
            TourState.CANCELLED,
            TourState.ERROR,
        }
    ),
    TourState.EXPLAINING: frozenset(
        {
            TourState.DEMONSTRATING,
            TourState.WAITING,
            TourState.NAVIGATING,
            TourState.PAUSED,
            TourState.CANCELLED,
            TourState.COMPLETED,
            TourState.ERROR,
        }
    ),
    TourState.DEMONSTRATING: frozenset(
        {
            TourState.WAITING,
            TourState.NAVIGATING,
            TourState.PAUSED,
            TourState.CANCELLED,
            TourState.COMPLETED,
            TourState.ERROR,
        }
    ),
    TourState.WAITING: frozenset(
        {
            TourState.NAVIGATING,
            TourState.EXPLAINING,
            TourState.PAUSED,
            TourState.CANCELLED,
            TourState.COMPLETED,
        }
    ),
    TourState.PAUSED: frozenset({TourState.NAVIGATING, TourState.EXPLAINING, TourState.CANCELLED}),
    TourState.ERROR: frozenset({TourState.CANCELLED, TourState.IDLE}),
    TourState.COMPLETED: frozenset({TourState.IDLE}),
    TourState.CANCELLED: frozenset({TourState.IDLE}),
}

# Type alias for command handlers.
_TourHandler = Callable[
    [TourContext, TourRequest, dict[str, Any]],
    Awaitable[TourResponse],
]


class TourService:
    """Orchestrate the guided platform tour with governance and cleanup.

    The tour uses the existing Conductor governance pipeline.  It never
    bypasses RBAC, approval, or audit.  All demo fixtures are temporary
    and cleaned up on tour end.
    """

    def __init__(
        self,
        *,
        governance: GovernancePolicy,
        audit: AuditLogger,
        fixture_service: TourFixtureService,
        memory_service: GovernedMemoryService | None = None,
    ) -> None:
        """Initialize the tour service with existing platform primitives."""
        self._governance = governance
        self._audit = audit
        self._fixtures = fixture_service
        self._memory = memory_service
        self._log = get_logger("eaip.copilot.tour")
        self._sessions: dict[str, TourContext] = {}

    def get_session(self, tour_session_id: str) -> TourContext | None:
        """Retrieve an active tour session by id."""
        return self._sessions.get(tour_session_id)

    def list_sessions(self, user_id: str) -> list[TourContext]:
        """List active tour sessions for a user."""
        return [s for s in self._sessions.values() if s.user_id == user_id]

    async def start_tour(
        self,
        user: dict[str, Any],
        *,
        theme: str = "light",
        voice_enabled: bool = False,
        permission_context: Any | None = None,
        current_route: str = "/",
    ) -> TourResponse:
        """Start a new guided tour for the authenticated user.

        Args:
            user: Authenticated user identity claims.
            theme: Current UI theme.
            voice_enabled: Whether voice narration is available.
            permission_context: Optional PermissionAwareContext for role filtering.
            current_route: Active frontend route for contextual tour starting.

        Returns:
            The initial tour response.
        """
        actor = self._actor(user)
        tenant = self._tenant(user)
        session_id = f"tour-{uuid.uuid4().hex[:12]}"
        steps = (
            get_dynamic_tour_steps(
                context=permission_context,
                start_route=current_route,
            )
            if (permission_context is not None or current_route != "/")
            else get_tour_steps()
        )

        already_completed = await self._check_tour_completed(user)

        context = TourContext(
            tour_session_id=session_id,
            user_id=actor,
            tenant_id=tenant,
            current_state=TourState.INTRO,
            current_step_index=0,
            current_route="/",
            current_application="enterprise_console",
            theme=theme,
            voice_enabled=voice_enabled,
            steps=steps,
            started_at=utc_now(),
        )
        self._sessions[session_id] = context

        self._audit.log(
            AuditEntry(
                id=f"audit-tour-start-{uuid.uuid4().hex[:12]}",
                actor_id=actor,
                action="tour.started",
                resource_type="tour_session",
                resource_id=session_id,
                outcome=AuditOutcome.SUCCESS,
                details={
                    "tenant_id": tenant,
                    "voice_enabled": voice_enabled,
                    "already_completed": already_completed,
                },
                correlation_id=str(CorrelationId.new()),
            )
        )

        first_step = steps[0] if steps else None
        intro_text = (
            "Hi, I'm your personal assistant. "
            "I'm going to show you how EAIP works. "
            "We'll walk through the major capabilities "
            "and I'll explain everything along the way."
        )
        if already_completed:
            intro_text = (
                "Welcome back! I see you've toured EAIP before. "
                "Would you like another walkthrough, "
                "or shall we skip ahead?"
            )

        return TourResponse(
            tour_session_id=session_id,
            state=TourState.INTRO,
            current_step=first_step,
            current_step_index=0,
            total_steps=len(steps),
            narration=intro_text,
            route=first_step.route if first_step else "/",
            application=(first_step.application if first_step else "enterprise_console"),
            voice_narration=intro_text,
        )

    async def process_command(
        self,
        tour_session_id: str,
        request: TourRequest,
        user: dict[str, Any],
    ) -> TourResponse:
        """Process a tour command from the user.

        Args:
            tour_session_id: The active tour session.
            request: The tour request with command and parameters.
            user: Authenticated user identity claims.

        Returns:
            The updated tour response.

        Raises:
            ValueError: If the session is unknown or command is invalid.
        """
        context = self._sessions.get(tour_session_id)
        if context is None:
            raise ValueError(f"Unknown tour session: {tour_session_id}")

        actor = self._actor(user)
        if context.user_id != actor:
            raise ValueError("Tour session does not belong to this user")

        command = request.command
        handler = self._get_handler(command)
        if handler is None:
            return self._error_response(context, f"Unknown command: {command}")

        result = await handler(context, request, user)
        self._sessions[tour_session_id] = context
        return result

    async def end_tour(
        self,
        tour_session_id: str,
        user: dict[str, Any],
        *,
        cancelled: bool = False,
    ) -> TourResponse:
        """End a tour session and clean up all fixtures.

        Args:
            tour_session_id: The tour session to end.
            user: Authenticated user identity claims.
            cancelled: Whether the tour was cancelled vs completed.

        Returns:
            The final tour response.
        """
        context = self._sessions.get(tour_session_id)
        if context is None:
            raise ValueError(f"Unknown tour session: {tour_session_id}")

        actor = self._actor(user)
        if context.user_id != actor:
            raise ValueError("Tour session does not belong to this user")

        terminal = TourState.CANCELLED if cancelled else TourState.COMPLETED
        context.current_state = terminal
        context.completed_at = utc_now()

        cleanup_errors: list[str] = []
        try:
            cleaned = await self._fixtures.cleanup_session(tour_session_id)
            self._log.info(
                "tour.cleanup.success",
                session_id=tour_session_id,
                count=len(cleaned),
            )
        except RuntimeError as exc:
            cleanup_errors.append(str(exc))
            self._log.error(
                "tour.cleanup.partial_failure",
                session_id=tour_session_id,
                error=str(exc),
            )

        self._audit.log(
            AuditEntry(
                id=f"audit-tour-end-{uuid.uuid4().hex[:12]}",
                actor_id=actor,
                action="tour.ended",
                resource_type="tour_session",
                resource_id=tour_session_id,
                outcome=(AuditOutcome.SUCCESS if not cleanup_errors else AuditOutcome.FAILURE),
                details={
                    "terminal_state": terminal.value,
                    "cleanup_errors": cleanup_errors,
                    "steps_visited": context.current_step_index,
                },
                correlation_id=str(CorrelationId.new()),
            )
        )

        if terminal is TourState.COMPLETED and self._memory is not None:
            try:
                await self._memory.create(
                    user,
                    content=("Completed the EAIP guided platform tour."),
                    domain=MemoryDomain.PERSONAL,
                    importance=0.4,
                    tags=("tour", "onboarding", "completed"),
                )
            except Exception as exc:
                self._log.warning("tour.memory.store_failed", error=str(exc))

        del self._sessions[tour_session_id]

        if terminal is TourState.COMPLETED:
            farewell = (
                "Tour complete! You've seen the major capabilities "
                "of EAIP. You can ask me anything about the platform "
                "at any time."
            )
        else:
            farewell = "Tour ended. You can start a new tour anytime by asking me."
        if cleanup_errors:
            farewell += (
                " Note: some demo fixture cleanup encountered "
                "errors. Please check the audit log for details."
            )

        return TourResponse(
            tour_session_id=tour_session_id,
            state=terminal,
            narration=farewell,
            voice_narration=farewell,
        )

    # --- Command handlers ---

    def _get_handler(self, command: TourCommand) -> _TourHandler | None:
        """Map a command to its handler method."""
        handlers: dict[TourCommand, _TourHandler] = {
            TourCommand.PAUSE: self._handle_pause,
            TourCommand.RESUME: self._handle_resume,
            TourCommand.NEXT: self._handle_next,
            TourCommand.PREVIOUS: self._handle_previous,
            TourCommand.SKIP: self._handle_skip,
            TourCommand.STOP: self._handle_stop,
            TourCommand.REPEAT: self._handle_repeat,
            TourCommand.EXPLAIN: self._handle_explain,
            TourCommand.EXPLAIN_SIMPLE: self._handle_explain_simple,
            TourCommand.WHAT_DOES_THIS_DO: self._handle_what_page,
            TourCommand.GO_TO: self._handle_go_to,
            TourCommand.TRY_MYSELF: self._handle_try_myself,
            TourCommand.MOST_IMPORTANT: self._handle_most_important,
        }
        return handlers.get(command)

    async def _handle_pause(
        self,
        ctx: TourContext,
        _req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Pause the active tour."""
        pausable = {
            TourState.NAVIGATING,
            TourState.EXPLAINING,
            TourState.DEMONSTRATING,
            TourState.WAITING,
        }
        if ctx.current_state not in pausable:
            return self._error_response(ctx, "Tour is not in a pausable state")
        ctx.current_state = TourState.PAUSED
        pause_text = "Tour paused. Say 'continue' or 'resume' when you're ready."
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.PAUSED,
            current_step=self._current_step(ctx),
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=pause_text,
            voice_narration=pause_text,
        )

    async def _handle_resume(
        self,
        ctx: TourContext,
        _req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Resume a paused tour."""
        if ctx.current_state is not TourState.PAUSED:
            return self._error_response(ctx, "Tour is not paused")
        ctx.current_state = TourState.EXPLAINING
        step = self._current_step(ctx)
        narration = f"Resuming. {step.narration}" if step else "Resuming tour."
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.EXPLAINING,
            current_step=step,
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=narration,
            route=step.route if step else "/",
            application=(step.application if step else "enterprise_console"),
            voice_narration=narration,
        )

    async def _handle_next(
        self, ctx: TourContext, _req: TourRequest, _user: dict[str, Any]
    ) -> TourResponse:
        """Advance to the next tour step."""
        return self._advance(ctx, 1)

    async def _handle_previous(
        self, ctx: TourContext, _req: TourRequest, _user: dict[str, Any]
    ) -> TourResponse:
        """Go back to the previous tour step."""
        return self._advance(ctx, -1)

    async def _handle_skip(
        self, ctx: TourContext, _req: TourRequest, _user: dict[str, Any]
    ) -> TourResponse:
        """Skip the current tour step."""
        return self._advance(ctx, 1)

    async def _handle_stop(
        self, ctx: TourContext, _req: TourRequest, user: dict[str, Any]
    ) -> TourResponse:
        """Stop and cancel the tour."""
        return await self.end_tour(ctx.tour_session_id, user, cancelled=True)

    async def _handle_repeat(
        self,
        ctx: TourContext,
        _req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Repeat the current step narration."""
        step = self._current_step(ctx)
        if step is None:
            return self._error_response(ctx, "No current step to repeat")
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.EXPLAINING,
            current_step=step,
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=step.narration,
            route=step.route,
            application=step.application,
            voice_narration=step.narration,
        )

    async def _handle_explain(
        self,
        ctx: TourContext,
        _req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Provide a detailed explanation of the current step."""
        step = self._current_step(ctx)
        if step is None:
            return self._error_response(ctx, "No current step to explain")
        explanation = f"{step.narration}\n\nWhy this matters: {step.why_it_matters}"
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.EXPLAINING,
            current_step=step,
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=explanation,
            route=step.route,
            application=step.application,
            voice_narration=step.narration,
        )

    async def _handle_explain_simple(
        self,
        ctx: TourContext,
        _req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Provide a simpler explanation of the current step."""
        step = self._current_step(ctx)
        if step is None:
            return self._error_response(ctx, "No current step")
        simple = f"{step.title}: {step.why_it_matters}"
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.EXPLAINING,
            current_step=step,
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=simple,
            route=step.route,
            application=step.application,
            voice_narration=simple,
        )

    async def _handle_what_page(
        self,
        ctx: TourContext,
        _req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Explain what the current page does."""
        step = self._current_step(ctx)
        if step is None:
            return self._error_response(ctx, "No current step")
        text = f"This is {step.title}. {step.why_it_matters}"
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.EXPLAINING,
            current_step=step,
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=text,
            route=step.route,
            application=step.application,
            voice_narration=text,
        )

    async def _handle_go_to(
        self,
        ctx: TourContext,
        req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Navigate to a specific tour step."""
        target = req.step_id or req.route
        if not target:
            return self._error_response(ctx, "Specify a step id or route to navigate to")
        step = get_step_by_id(target)
        if step is None and target.startswith("/"):
            for s in ctx.steps:
                if s.route == target:
                    step = s
                    break
        if step is None:
            return self._error_response(ctx, f"Step '{target}' not found in tour")
        ctx.current_step_index = step.order
        ctx.current_state = TourState.NAVIGATING
        narration = f"Navigating to {step.title}. {step.narration}"
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.NAVIGATING,
            current_step=step,
            current_step_index=step.order,
            total_steps=len(ctx.steps),
            narration=narration,
            route=step.route,
            application=step.application,
            voice_narration=f"Going to {step.title}.",
        )

    async def _handle_try_myself(
        self,
        ctx: TourContext,
        _req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Let the user try the current feature themselves."""
        step = self._current_step(ctx)
        ctx.current_state = TourState.WAITING
        text = (
            "Go ahead, try it yourself! I'll be here when "
            "you're ready to continue. Say 'continue' or 'next' "
            "when you want to move on."
        )
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.WAITING,
            current_step=step,
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=text,
            route=step.route if step else "/",
            application=(step.application if step else "enterprise_console"),
            voice_narration=text,
        )

    async def _handle_most_important(
        self,
        ctx: TourContext,
        _req: TourRequest,
        _user: dict[str, Any],
    ) -> TourResponse:
        """Highlight the most important thing about EAIP."""
        step = self._current_step(ctx)
        text = (
            "The most important thing to understand about EAIP "
            "is the Conductor — your personal assistant. It's the "
            "governed AI that ties everything together. Every action "
            "goes through governance, approval, and audit."
        )
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.EXPLAINING,
            current_step=step,
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=text,
            voice_narration=text,
        )

    # --- Helpers ---

    def _advance(self, ctx: TourContext, delta: int) -> TourResponse:
        """Advance or retreat through tour steps."""
        new_index = ctx.current_step_index + delta
        if new_index < 0:
            return self._error_response(ctx, "Already at the first step")
        if new_index >= len(ctx.steps):
            ctx.current_state = TourState.COMPLETED
            ctx.completed_at = utc_now()
            farewell = (
                "That's the end of the tour! You've seen all the "
                "major capabilities of EAIP. You can ask me anything "
                "about the platform at any time."
            )
            return TourResponse(
                tour_session_id=ctx.tour_session_id,
                state=TourState.COMPLETED,
                current_step_index=ctx.current_step_index,
                total_steps=len(ctx.steps),
                narration=farewell,
                voice_narration=farewell,
            )
        ctx.current_step_index = new_index
        ctx.current_state = TourState.NAVIGATING
        step = ctx.steps[new_index]
        ctx.current_route = step.route
        ctx.current_application = step.application
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=TourState.NAVIGATING,
            current_step=step,
            current_step_index=new_index,
            total_steps=len(ctx.steps),
            narration=step.narration,
            route=step.route,
            application=step.application,
            voice_narration=step.narration,
        )

    def _current_step(self, ctx: TourContext) -> TourStep | None:
        """Return the current step or None if out of bounds."""
        if 0 <= ctx.current_step_index < len(ctx.steps):
            return ctx.steps[ctx.current_step_index]
        return None

    def _error_response(self, ctx: TourContext, message: str) -> TourResponse:
        """Build an error response preserving current state."""
        return TourResponse(
            tour_session_id=ctx.tour_session_id,
            state=ctx.current_state,
            current_step=self._current_step(ctx),
            current_step_index=ctx.current_step_index,
            total_steps=len(ctx.steps),
            narration=message,
            error=message,
        )

    @staticmethod
    def _actor(user: dict[str, Any]) -> str:
        """Extract the actor id from identity claims."""
        return str(user.get("sub") or user.get("name") or "unknown")

    @staticmethod
    def _tenant(user: dict[str, Any]) -> str:
        """Extract the tenant id from identity claims."""
        return str(
            user.get("organization_id") or user.get("org_id") or user.get("tenant_id") or "default"
        )

    async def _check_tour_completed(self, user: dict[str, Any]) -> bool:
        """Check governed memory for prior tour completion."""
        if self._memory is None:
            return False
        try:
            items = await self._memory.retrieve(
                user,
                "EAIP guided platform tour completed",
                limit=1,
            )
            return len(items) > 0
        except Exception:
            return False


__all__ = ["TourService"]
