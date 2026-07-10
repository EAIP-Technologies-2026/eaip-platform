"""Context & Session Intelligence — session management, context propagation, lifecycle."""

from __future__ import annotations

from eaip.session.context_manager import EnterpriseContextManager
from eaip.session.events import (
    ContextAttributeSet,
    ContextPropagated,
    SessionClosed,
    SessionCreated,
    SessionExpired,
    SessionResumed,
    SessionSuspended,
    SessionTransferred,
    SessionUpdated,
)
from eaip.session.exceptions import (
    ContextError,
    SessionError,
    SessionExpiredError,
    SessionLimitError,
    SessionNotFoundError,
)
from eaip.session.health import SessionHealthCheck
from eaip.session.integration import SessionRuntimeModule, create_session_integration
from eaip.session.lifecycle import SessionLifecycleManager
from eaip.session.manager import SessionManager
from eaip.session.models import (
    ContextPropagationConfig,
    ContextScope,
    ExecutionContext,
    Session,
    SessionConfig,
    SessionContext,
)
from eaip.session.serialization import SessionSerializer

__all__ = [
    "ContextAttributeSet",
    "ContextError",
    "ContextPropagated",
    "ContextPropagationConfig",
    "ContextScope",
    "EnterpriseContextManager",
    "ExecutionContext",
    "Session",
    "SessionClosed",
    "SessionConfig",
    "SessionContext",
    "SessionCreated",
    "SessionError",
    "SessionExpired",
    "SessionExpiredError",
    "SessionHealthCheck",
    "SessionLifecycleManager",
    "SessionLimitError",
    "SessionManager",
    "SessionNotFoundError",
    "SessionResumed",
    "SessionRuntimeModule",
    "SessionSerializer",
    "SessionSuspended",
    "SessionTransferred",
    "SessionUpdated",
    "create_session_integration",
]
