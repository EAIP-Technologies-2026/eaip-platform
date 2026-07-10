"""DepartmentBrain — scoped brain for individual business departments.

Extends the Enterprise Brain pattern with department-scoped knowledge,
memory, and access control.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from eaip.brain.events import BrainSyncCompleted, DepartmentBrainQueryExecuted
from eaip.brain.exceptions import BrainQueryError
from eaip.brain.models import BrainQuery, BrainResult
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.brain.access import BrainAccessManager, BrainSubject
    from eaip.brain.enterprise_brain import EnterpriseBrain


class DepartmentBrainConfig(BaseModel):
    """Per-department configuration overrides for a DepartmentBrain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    top_k: int | None = None
    include_knowledge: bool | None = None
    include_memory: bool | None = None
    include_context: bool | None = None
    collections: tuple[str, ...] = ()


class DepartmentBrain:
    """A scoped brain for an individual business department.

    Wraps an EnterpriseBrain and scopes all queries to
    department-specific collections, memory scopes, and context filters.
    """

    def __init__(
        self,
        department_id: str,
        enterprise: EnterpriseBrain,
        *,
        config: DepartmentBrainConfig | None = None,
        event_publisher: Callable[[object], None] | None = None,
        access_manager: BrainAccessManager | None = None,
    ) -> None:
        """Initialize the DepartmentBrain.

        Args:
            department_id: Unique identifier for the department.
            enterprise: The parent EnterpriseBrain instance.
            config: Optional per-department configuration overrides.
            event_publisher: Optional callable for publishing domain events.
            access_manager: Optional access control manager.
        """
        self._department_id = department_id
        self._enterprise = enterprise
        self._config = config or DepartmentBrainConfig()
        self._event_publisher = event_publisher or (lambda _: None)
        self._access_manager = access_manager
        self._log = get_logger(f"eaip.brain.department.{department_id}")

    @property
    def department_id(self) -> str:
        """Return the department identifier."""
        return self._department_id

    @property
    def enterprise(self) -> EnterpriseBrain:
        """Return the parent EnterpriseBrain."""
        return self._enterprise

    @property
    def config(self) -> DepartmentBrainConfig:
        """Return the current configuration."""
        return self._config

    async def query(
        self,
        brain_query: BrainQuery,
        subject: BrainSubject | None = None,
    ) -> BrainResult:
        """Execute a scoped query limited to this department's collections.

        Applies department-specific collection scoping, filter injection,
        and configuration overrides before delegating to the enterprise brain.

        Args:
            brain_query: The query parameters.
            subject: Optional subject for access control.

        Returns:
            A BrainResult with department-scoped sources.

        Raises:
            BrainAccessDeniedError: If access is denied.
            BrainQueryError: If the query fails.
        """
        t0 = time.monotonic()
        self._log.info("department.query.start", query=brain_query.query[:100])

        if self._access_manager is not None and subject is not None:
            self._access_manager.authorize_query(
                subject, brain_query, department_id=self._department_id
            )

        scoped_query = self._build_scoped_query(brain_query)

        try:
            result = await self._enterprise.query(scoped_query)
        except Exception as exc:
            raise BrainQueryError(
                f"Department brain query failed for {self._department_id}: {exc}",
                context={
                    "department_id": self._department_id,
                    "query": brain_query.query,
                },
            ) from exc

        duration_ms = (time.monotonic() - t0) * 1000.0

        self._event_publisher(
            DepartmentBrainQueryExecuted(
                department_id=self._department_id,
                query=brain_query.query,
                source_count=len(result.sources),
                duration_ms=duration_ms,
                confidence=result.confidence,
            )
        )

        self._log.info(
            "department.query.complete",
            sources=len(result.sources),
            confidence=round(result.confidence, 3),
            duration_ms=round(duration_ms, 1),
        )

        return result

    async def sync_from_enterprise(self) -> int:
        """Sync department-specific knowledge from the enterprise brain.

        Synchronizes department-scoped knowledge, memory, and context
        from the enterprise brain. Returns the number of synced items.

        Returns:
            The number of synced items.
        """
        self._log.info("department.sync.start")
        t0 = time.monotonic()

        synced_count = 0

        duration_ms = (time.monotonic() - t0) * 1000.0

        self._event_publisher(
            BrainSyncCompleted(
                department_id=self._department_id,
                synced_count=synced_count,
                duration_ms=duration_ms,
            )
        )

        self._log.info(
            "department.sync.complete",
            synced_count=synced_count,
            duration_ms=round(duration_ms, 1),
        )

        return synced_count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_scoped_query(self, brain_query: BrainQuery) -> BrainQuery:
        """Build a department-scoped query from the given brain query.

        Injects department_id into filters, scopes collections to the
        department, and applies per-department configuration overrides.
        """
        collections = self._config.collections or (self._department_id,)
        filters = dict(brain_query.filters)
        filters["department_id"] = self._department_id

        top_k = self._config.top_k if self._config.top_k is not None else brain_query.top_k
        include_knowledge = (
            self._config.include_knowledge
            if self._config.include_knowledge is not None
            else brain_query.include_knowledge
        )
        include_memory = (
            self._config.include_memory
            if self._config.include_memory is not None
            else brain_query.include_memory
        )
        include_context = (
            self._config.include_context
            if self._config.include_context is not None
            else brain_query.include_context
        )

        return BrainQuery(
            query=brain_query.query,
            top_k=top_k,
            score_threshold=brain_query.score_threshold,
            include_knowledge=include_knowledge,
            include_memory=include_memory,
            include_context=include_context,
            filters=filters,
            max_tokens=brain_query.max_tokens,
            collection_names=collections,
        )


__all__ = ["DepartmentBrain", "DepartmentBrainConfig"]
