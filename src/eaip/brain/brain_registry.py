"""BrainRegistry — central registry for department and enterprise brains."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import TYPE_CHECKING

from eaip.brain.department_brain import DepartmentBrain
from eaip.brain.enterprise_brain import EnterpriseBrain
from eaip.brain.models import BrainQuery, BrainResult
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    pass


class BrainRegistry:
    """Central registry that manages enterprise and department brains.

    Provides methods to register, retrieve, and query department brains
    as well as access to the enterprise brain.
    """

    def __init__(self, enterprise: EnterpriseBrain | None = None) -> None:
        """Initialize the BrainRegistry.

        Args:
            enterprise: Optional EnterpriseBrain instance.
        """
        self._enterprise = enterprise
        self._departments: dict[str, DepartmentBrain] = {}
        self._log = get_logger("eaip.brain.registry")

    def register_department(self, department_id: str, brain: DepartmentBrain) -> None:
        """Register a department brain.

        Args:
            department_id: The unique department identifier.
            brain: The DepartmentBrain instance.

        Raises:
            ValueError: If the department is already registered.
        """
        if department_id in self._departments:
            raise ValueError(
                f"Department '{department_id}' is already registered in BrainRegistry"
            )
        self._departments[department_id] = brain
        self._log.info("registry.department.registered", department_id=department_id)

    def get_department(self, department_id: str) -> DepartmentBrain:
        """Get a registered department brain.

        Args:
            department_id: The department identifier.

        Returns:
            The DepartmentBrain instance.

        Raises:
            KeyError: If the department is not registered.
        """
        if department_id not in self._departments:
            raise KeyError(f"Department '{department_id}' not found in BrainRegistry")
        return self._departments[department_id]

    def get_enterprise(self) -> EnterpriseBrain:
        """Get the enterprise brain.

        Returns:
            The EnterpriseBrain instance.

        Raises:
            RuntimeError: If no enterprise brain is configured.
        """
        if self._enterprise is None:
            raise RuntimeError("EnterpriseBrain not configured in BrainRegistry")
        return self._enterprise

    def list_departments(self) -> tuple[str, ...]:
        """List all registered department IDs.

        Returns:
            A tuple of department IDs.
        """
        return tuple(self._departments.keys())

    async def query_all(
        self, query: str, top_k: int = 10
    ) -> dict[str, BrainResult]:
        """Query all registered department brains in parallel.

        Args:
            query: The query string.
            top_k: Maximum number of results per department.

        Returns:
            A dict mapping department_id to BrainResult.
        """
        if not self._departments:
            return {}

        brain_query = BrainQuery(query=query, top_k=top_k)

        async def _query(dept_id: str, brain: DepartmentBrain) -> tuple[str, BrainResult | None]:
            try:
                result = await brain.query(brain_query)
                return dept_id, result
            except Exception as exc:
                self._log.warning(
                    "registry.query_all.failed",
                    department_id=dept_id,
                    error=str(exc),
                )
                return dept_id, None

        coros = [_query(did, b) for did, b in self._departments.items()]
        outcomes = await asyncio.gather(*coros)

        results: dict[str, BrainResult] = {}
        for dept_id, result in outcomes:
            if result is not None:
                results[dept_id] = result

        return results

    async def query_departments(
        self,
        department_ids: Sequence[str],
        query: str,
        top_k: int = 10,
    ) -> dict[str, BrainResult]:
        """Query specific department brains in parallel.

        Args:
            department_ids: The department IDs to query.
            query: The query string.
            top_k: Maximum number of results per department.

        Returns:
            A dict mapping department_id to BrainResult.
        """
        brain_query = BrainQuery(query=query, top_k=top_k)

        async def _query(dept_id: str) -> tuple[str, BrainResult | None]:
            try:
                brain = self.get_department(dept_id)
                result = await brain.query(brain_query)
                return dept_id, result
            except (KeyError, Exception) as exc:
                self._log.warning(
                    "registry.query_departments.failed",
                    department_id=dept_id,
                    error=str(exc),
                )
                return dept_id, None

        coros = [_query(did) for did in department_ids]
        outcomes = await asyncio.gather(*coros)

        results: dict[str, BrainResult] = {}
        for dept_id, result in outcomes:
            if result is not None:
                results[dept_id] = result

        return results


__all__ = ["BrainRegistry"]
