"""Provider-based observability layer.

Integrates Sentry, Better Stack, and future backends through a common
``ObservabilityProvider`` protocol. Providers are registered centrally and
managed as a lifecycle-aware composite.
"""

from eaip.observability.manager import (
    ObservabilityManager,
    build_observability_manager,
)

__all__ = [
    "ObservabilityManager",
    "build_observability_manager",
]
