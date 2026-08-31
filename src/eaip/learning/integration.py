"""Platform integration for the Organizational Learning Engine."""

from __future__ import annotations

from typing import Any

from eaip.learning.adaptation import AdaptationEngine
from eaip.learning.engine import OrganizationalLearningEngine
from eaip.learning.feedback_loop import FeedbackLoop
from eaip.learning.models import LearningSource
from eaip.learning.persistence import LearningStore
from eaip.logging.context import get_logger


def create_learning_engine(
    event_publisher: object | None = None,
) -> tuple[OrganizationalLearningEngine, FeedbackLoop, AdaptationEngine]:
    """Create and wire the learning subsystem components.

    Returns:
        A tuple of (learning_engine, feedback_loop, adaptation_engine).
    """
    store = LearningStore()
    engine = OrganizationalLearningEngine(store=store, event_publisher=event_publisher)
    feedback = FeedbackLoop(store=store, event_publisher=event_publisher, learning_engine=engine)
    adaptation = AdaptationEngine(store=store, event_publisher=event_publisher)
    return engine, feedback, adaptation


__all__ = ["create_learning_engine"]
