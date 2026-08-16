"""Runtime integration for Intelligence Pulse."""

from __future__ import annotations

from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.infrastructure.persistence.pulse import PulseRepository
from eaip.pulse.engine import PulseEngine
from eaip.runtime.modules import RuntimeModule


class PulseRuntimeModule(RuntimeModule):
    """Runtime module providing Intelligence Pulse capabilities."""

    @property
    def name(self) -> str:
        return "pulse"

    def register(self, container: Any) -> None:
        """Register pulse dependencies."""
        db = container.resolve(DatabaseConnection)
        repository = PulseRepository(db)
        container.register_instance(PulseRepository, repository)

        engine = PulseEngine(repository=repository)
        container.register_instance(PulseEngine, engine)
