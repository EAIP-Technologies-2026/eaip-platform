"""Runtime integration for Decision Intelligence."""

from __future__ import annotations

from typing import Any

from eaip.decisions.engine import DecisionEngine
from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence.decisions import DecisionRepository
from eaip.runtime.modules import RuntimeModule


class DecisionRuntimeModule(RuntimeModule):
    """Runtime module providing Decision Intelligence capabilities."""

    @property
    def name(self) -> str:
        return "decisions"

    def register(self, container: Any) -> None:
        """Register decision dependencies."""
        db = container.resolve(DatabaseConnection)
        repository = DecisionRepository(db)
        container.register_instance(DecisionRepository, repository)

        engine = DecisionEngine(repository=repository)
        container.register_instance(DecisionEngine, engine)
