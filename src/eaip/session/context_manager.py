"""EnterpriseContextManager — scope-based context propagation and management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eaip.context.builder import ContextBuilder
from eaip.logging.context import get_logger
from eaip.session.events import ContextAttributeSet, ContextPropagated
from eaip.session.exceptions import ContextError
from eaip.session.models import (
    ContextPropagationConfig,
    ContextScope,
    ExecutionContext,
    Session,
    SessionContext,
)
from eaip.session.serialization import SessionSerializer
from eaip.shared.time import utc_now


class ScopedStore:
    """An in-memory store mapping (scope, scope_id) to attribute dictionaries."""

    def __init__(self) -> None:
        """Initialize the scoped store."""
        self._store: dict[tuple[str, str], dict[str, Any]] = {}

    def get_context(self, scope: str, scope_id: str) -> dict[str, Any]:
        """Return the attribute dict for a given scope, creating if absent.

        Args:
            scope: The scope name.
            scope_id: The scope identifier.

        Returns:
            The attribute dictionary for the scope.
        """
        key = (scope, scope_id)
        if key not in self._store:
            self._store[key] = {}
        return self._store[key]

    def set_attribute(self, scope: str, scope_id: str, key: str, value: Any) -> None:
        """Set an attribute in the given scope.

        Args:
            scope: The scope name.
            scope_id: The scope identifier.
            key: The attribute key.
            value: The attribute value.
        """
        ctx = self.get_context(scope, scope_id)
        ctx[key] = value

    def get_attribute(self, scope: str, scope_id: str, key: str) -> Any | None:
        """Get an attribute from the given scope.

        Args:
            scope: The scope name.
            scope_id: The scope identifier.
            key: The attribute key.

        Returns:
            The attribute value, or None if not found.
        """
        ctx = self.get_context(scope, scope_id)
        return ctx.get(key)

    def clear_context(self, scope: str, scope_id: str) -> None:
        """Clear all attributes for a scope.

        Args:
            scope: The scope name.
            scope_id: The scope identifier.
        """
        key = (scope, scope_id)
        if key in self._store:
            self._store[key] = {}

    def clear_all(self) -> None:
        """Clear all stored scopes."""
        self._store.clear()


class EnterpriseContextManager:
    """Manages context at multiple enterprise scopes and propagates between sessions.

    Integrates with ContextBuilder for assembling rich context payloads.
    """

    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        event_publisher: Any = None,
    ) -> None:
        """Initialize the EnterpriseContextManager.

        Args:
            context_builder: Optional ContextBuilder for assembling context.
            event_publisher: Optional callable for publishing domain events.
        """
        self._store = ScopedStore()
        self._context_builder = context_builder
        self._event_publisher = event_publisher or (lambda _: None)
        self._log = get_logger("eaip.session.context_manager")

    async def get_context(
        self,
        scope: str,
        scope_id: str,
    ) -> dict[str, Any]:
        """Get the full context for a given scope.

        Args:
            scope: The scope name (validated against ContextScope).
            scope_id: The scope identifier.

        Returns:
            The attribute dictionary for the scope.
        """
        ContextScope(scope)
        return self._store.get_context(scope, scope_id)

    async def set_attribute(
        self,
        scope: str,
        scope_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Set a context attribute at the given scope.

        Args:
            scope: The scope name.
            scope_id: The scope identifier.
            key: The attribute key.
            value: The attribute value.
        """
        ContextScope(scope)
        self._store.set_attribute(scope, scope_id, key, value)
        self._event_publisher(
            ContextAttributeSet(scope=scope, scope_id=scope_id, key=key, value=value)
        )
        self._log.debug("context.attribute.set", scope=scope, scope_id=scope_id, key=key)

    async def get_attribute(
        self,
        scope: str,
        scope_id: str,
        key: str,
    ) -> Any | None:
        """Get a context attribute from the given scope.

        Args:
            scope: The scope name.
            scope_id: The scope identifier.
            key: The attribute key.

        Returns:
            The attribute value, or None if not found.
        """
        ContextScope(scope)
        return self._store.get_attribute(scope, scope_id, key)

    async def clear_context(self, scope: str, scope_id: str) -> None:
        """Clear all context attributes for a given scope.

        Args:
            scope: The scope name.
            scope_id: The scope identifier.
        """
        ContextScope(scope)
        self._store.clear_context(scope, scope_id)
        self._log.debug("context.cleared", scope=scope, scope_id=scope_id)

    async def propagate_context(
        self,
        source_session: Session,
        target_ids: list[str],
        config: ContextPropagationConfig | None = None,
    ) -> None:
        """Propagate context from a source session to target sessions.

        Copies the source session's context_snapshot into the context
        store of each target, respecting the propagation configuration.

        Args:
            source_session: The source Session.
            target_ids: A list of target session identifiers.
            config: Optional propagation configuration.

        Raises:
            ContextError: If propagation fails.
        """
        cfg = config or ContextPropagationConfig()
        snapshot = source_session.context_snapshot

        if cfg.allowed_attributes:
            snapshot = {
                k: v for k, v in snapshot.items()
                if k in cfg.allowed_attributes
            }

        depth = 0
        for tid in target_ids:
            if cfg.max_depth > 0 and depth >= cfg.max_depth:
                break
            scope = ContextScope.EXECUTION
            for key, value in snapshot.items():
                self._store.set_attribute(scope.value, tid, key, value)
            depth += 1

        self._event_publisher(
            ContextPropagated(
                source_session_id=source_session.id,
                target_ids=target_ids,
                attribute_count=len(snapshot),
            )
        )
        self._log.info(
            "context.propagated",
            source=source_session.id,
            targets=len(target_ids),
            attributes=len(snapshot),
        )

    async def build_session_context(self, session_id: str) -> SessionContext:
        """Build a full SessionContext for the given session ID.

        Gathers attributes from enterprise, tenant, user, workflow,
        agent, and execution scopes and returns a consolidated context.

        Args:
            session_id: The session identifier.

        Returns:
            A SessionContext with aggregated attributes.
        """
        all_attrs: dict[str, Any] = {}

        for scope in ContextScope:
            scope_attrs = self._store.get_context(scope.value, session_id)
            all_attrs.update(scope_attrs)

        context = SessionContext(
            session_id=session_id,
            attributes=all_attrs,
            created_at=utc_now(),
        )

        self._log.debug("context.built", session_id=session_id, attributes=len(all_attrs))
        return context


__all__ = ["EnterpriseContextManager", "ScopedStore"]
