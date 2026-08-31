"""Runtime integration for Recommendations."""

from __future__ import annotations

from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence.recommendations import RecommendationRepository
from eaip.recommendations.engine import RecommendationEngine
from eaip.runtime.module import RuntimeModule


class RecommendationRuntimeModule(RuntimeModule):
    """Runtime module providing Recommendations capabilities."""

    @property
    def name(self) -> str:
        return "recommendations"

    def register(self, container: Any) -> None:
        """Register recommendation dependencies."""
        db = container.resolve(DatabaseConnection)
        repository = RecommendationRepository(db)
        container.register_instance(RecommendationRepository, repository)

        engine = RecommendationEngine(repository=repository)
        container.register_instance(RecommendationEngine, engine)
