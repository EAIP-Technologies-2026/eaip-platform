"""EP-0144 — Customer Feedback Analyzer — sentiment & aggregation pipeline."""

from __future__ import annotations

from eaip.custfeedback.analyzer import FeedbackAnalyzer
from eaip.custfeedback.events import (
    FeedbackAggregated,
    FeedbackAnalyzed,
    FeedbackSubmitted,
)
from eaip.custfeedback.exceptions import (
    FeedbackError,
    FeedbackNotFoundError,
)
from eaip.custfeedback.health import FeedbackHealthCheck
from eaip.custfeedback.integration import FeedbackRuntimeModule
from eaip.custfeedback.models import (
    AnalyzerConfig,
    FeedbackAggregate,
    FeedbackItem,
)

__all__ = [
    "AnalyzerConfig",
    "FeedbackAggregate",
    "FeedbackAggregated",
    "FeedbackAnalyzed",
    "FeedbackAnalyzer",
    "FeedbackError",
    "FeedbackHealthCheck",
    "FeedbackItem",
    "FeedbackNotFoundError",
    "FeedbackRuntimeModule",
    "FeedbackSubmitted",
]
