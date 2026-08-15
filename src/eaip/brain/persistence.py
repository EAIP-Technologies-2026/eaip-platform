"""Second Brain persistence repositories.

Reuses the existing EAIP PostgreSQL + asyncpg access pattern (no ORM).

A :class:`SecondBrainRepository` abstracts durable storage so the service can
fall back to in-memory state when no database is configured, while using
:class:`SqlSecondBrainRepository` (asyncpg) when a pool is available.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from eaip.brain.second_brain import SecondBrain
from eaip.infrastructure.db.connection import DatabaseConnection


class SecondBrainRepository(ABC):
    """Durable store abstraction for governed brains."""

    @abstractmethod
    async def save(self, brain: SecondBrain) -> None: ...

    @abstractmethod
    async def get(self, brain_id: str) -> SecondBrain | None: ...

    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> list[SecondBrain]: ...

    @abstractmethod
    async def delete(self, brain_id: str) -> None: ...


_COLUMNS = (
    "id",
    "name",
    "description",
    "business_function",
    "owner_id",
    "organization_id",
    "status",
    "objectives",
    "instructions",
    "knowledge_sources",
    "rules",
    "tools",
    "approval_required",
    "recommendations",
    "mission_ids",
    "memory_ids",
    "activity",
    "created_at",
    "updated_at",
)


def _row_to_brain(row: Any) -> SecondBrain:
    return SecondBrain.from_row(row)


class SqlSecondBrainRepository(SecondBrainRepository):
    """asyncpg-backed repository using the shared EAIP database pool."""

    async def save(self, brain: SecondBrain) -> None:
        await DatabaseConnection.execute(
            """
            INSERT INTO second_brains (
                id, name, description, business_function, owner_id, organization_id,
                status, objectives, instructions, knowledge_sources, rules, tools,
                approval_required, recommendations, mission_ids, memory_ids, activity,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7,
                $8::jsonb, $9, $10::jsonb, $11::jsonb, $12::jsonb,
                $13, $14::jsonb, $15::jsonb, $16::jsonb, $17::jsonb,
                $18, $19
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                business_function = EXCLUDED.business_function,
                organization_id = EXCLUDED.organization_id,
                status = EXCLUDED.status,
                objectives = EXCLUDED.objectives,
                instructions = EXCLUDED.instructions,
                knowledge_sources = EXCLUDED.knowledge_sources,
                rules = EXCLUDED.rules,
                tools = EXCLUDED.tools,
                approval_required = EXCLUDED.approval_required,
                recommendations = EXCLUDED.recommendations,
                mission_ids = EXCLUDED.mission_ids,
                memory_ids = EXCLUDED.memory_ids,
                activity = EXCLUDED.activity,
                updated_at = EXCLUDED.updated_at
            """,
            brain.brain_id,
            brain.name,
            brain.description,
            brain.business_function,
            brain.owner_id,
            brain.organization_id,
            brain.status,
            json.dumps(brain.objectives),
            brain.instructions,
            json.dumps(brain.knowledge_sources),
            json.dumps(brain.rules),
            json.dumps(brain.tools),
            brain.approval_required,
            json.dumps(brain.recommendations),
            json.dumps(brain.mission_ids),
            json.dumps(brain.memory_ids),
            json.dumps(brain.activity),
            brain.created_at,
            brain.updated_at,
        )

    async def get(self, brain_id: str) -> SecondBrain | None:
        row = await DatabaseConnection.fetchrow(
            f"SELECT {', '.join(_COLUMNS)} FROM second_brains WHERE id = $1", brain_id
        )
        return _row_to_brain(row) if row is not None else None

    async def list_by_owner(self, owner_id: str) -> list[SecondBrain]:
        rows = await DatabaseConnection.fetch(
            f"SELECT {', '.join(_COLUMNS)} FROM second_brains WHERE owner_id = $1 "
            "ORDER BY created_at DESC",
            owner_id,
        )
        return [_row_to_brain(row) for row in rows]

    async def delete(self, brain_id: str) -> None:
        await DatabaseConnection.execute("DELETE FROM second_brains WHERE id = $1", brain_id)


class InMemorySecondBrainRepository(SecondBrainRepository):
    """Process-local repository used when no database is configured.

    Useful for tests and as a safe fallback so the service never loses state
    if the database is unavailable.
    """

    def __init__(self) -> None:
        self._store: dict[str, SecondBrain] = {}

    async def save(self, brain: SecondBrain) -> None:
        self._store[brain.brain_id] = brain

    async def get(self, brain_id: str) -> SecondBrain | None:
        return self._store.get(brain_id)

    async def list_by_owner(self, owner_id: str) -> list[SecondBrain]:
        return [b for b in self._store.values() if b.owner_id == owner_id]

    async def delete(self, brain_id: str) -> None:
        self._store.pop(brain_id, None)


__all__ = [
    "InMemorySecondBrainRepository",
    "SecondBrainRepository",
    "SqlSecondBrainRepository",
]
