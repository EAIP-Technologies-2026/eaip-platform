"""API composition — aggregate multiple source endpoints into one response."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from eaip.apiext.events import CompositionExecuted
from eaip.apiext.exceptions import CompositionError
from eaip.apiext.models import ApiComposition, MergeStrategy
from eaip.logging.context import get_logger


class ApiComposer:
    """Registers and executes API compositions that aggregate multiple endpoints."""

    def __init__(self) -> None:
        """Initialize the composer with an empty composition registry."""
        self._compositions: dict[str, ApiComposition] = {}
        self._log = get_logger("eaip.apiext.composition")

    def register_composition(self, composition: ApiComposition) -> None:
        """Register a new composition.

        Args:
            composition: The composition definition.

        Raises:
            CompositionError: If a composition with the same id already exists.
        """
        if composition.id in self._compositions:
            raise CompositionError(
                f"Composition '{composition.id}' is already registered.",
                context={"composition_id": composition.id},
            )
        self._compositions[composition.id] = composition
        self._log.info(
            "apiext.composition.registered",
            composition_id=composition.id,
            endpoint_path=composition.endpoint_path,
        )

    def unregister_composition(self, composition_id: str) -> None:
        """Remove a previously registered composition.

        Args:
            composition_id: The composition identifier.

        Raises:
            CompositionError: If the composition is not found.
        """
        if composition_id not in self._compositions:
            raise CompositionError(
                f"Composition '{composition_id}' is not registered.",
                context={"composition_id": composition_id},
            )
        del self._compositions[composition_id]
        self._log.info(
            "apiext.composition.unregistered",
            composition_id=composition_id,
        )

    def get_composition(self, composition_id: str) -> ApiComposition | None:
        """Look up a composition by identifier.

        Args:
            composition_id: The composition identifier.

        Returns:
            The matching composition, or ``None``.
        """
        return self._compositions.get(composition_id)

    def list_compositions(self) -> list[ApiComposition]:
        """Return all registered compositions.

        Returns:
            A list of all compositions.
        """
        return list(self._compositions.values())

    async def execute_composition(
        self,
        composition: ApiComposition,
        request_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a composition by fetching all source endpoints concurrently.

        Args:
            composition: The composition to execute.
            request_context: Optional context passed to source fetchers.

        Returns:
            The merged response from all source endpoints.

        Raises:
            CompositionError: If execution fails.
        """
        if not composition.enabled:
            raise CompositionError(
                f"Composition '{composition.id}' is disabled.",
                context={"composition_id": composition.id},
            )

        t0 = time.monotonic()
        ctx = request_context or {}
        source_count = len(composition.source_endpoints)

        async def _fetch_source(source: str) -> dict[str, Any]:
            try:
                return await asyncio.wait_for(
                    self._fetch(source, ctx),
                    timeout=composition.timeout_seconds,
                )
            except TimeoutError:
                raise CompositionError(
                    f"Source endpoint '{source}' timed out after {composition.timeout_seconds}s",
                    context={"composition_id": composition.id, "source": source},
                )

        try:
            results = await asyncio.gather(
                *[_fetch_source(s) for s in composition.source_endpoints],
                return_exceptions=False,
            )
        except CompositionError:
            duration_ms = (time.monotonic() - t0) * 1000
            CompositionExecuted(
                composition_id=composition.id,
                composition_name=composition.name,
                endpoint_path=composition.endpoint_path,
                method=composition.method,
                duration_ms=duration_ms,
                source_count=source_count,
                success=False,
            )
            raise

        merged = self._merge_results(results, composition.merge_strategy)

        if composition.response_mapping:
            merged = self._apply_mapping(merged, composition.response_mapping)

        duration_ms = (time.monotonic() - t0) * 1000
        CompositionExecuted(
            composition_id=composition.id,
            composition_name=composition.name,
            endpoint_path=composition.endpoint_path,
            method=composition.method,
            duration_ms=duration_ms,
            source_count=source_count,
            success=True,
        )

        return merged

    async def _fetch(self, source: str, context: dict[str, Any]) -> dict[str, Any]:
        """Simulate fetching a single source endpoint.

        In production this would perform an HTTP request; for the base
        implementation it returns a placeholder response.

        Args:
            source: The source endpoint path.
            context: Request context.

        Returns:
            A dict representing the source response.
        """
        return {"source": source, "context": context}

    def _merge_results(
        self,
        results: list[dict[str, Any]],
        strategy: MergeStrategy,
    ) -> dict[str, Any]:
        """Merge multiple source results using the given strategy.

        Args:
            results: List of source response dicts.
            strategy: The merge strategy to apply.

        Returns:
            The merged result dict.
        """
        if strategy == MergeStrategy.CONCAT:
            merged: dict[str, Any] = {}
            for i, r in enumerate(results):
                merged[f"source_{i}"] = r
            return merged

        if strategy == MergeStrategy.MERGE:
            merged = {}
            for r in results:
                merged.update(r)
            return merged

        if strategy == MergeStrategy.ZIP:
            max_len = max(len(r) if isinstance(r, dict) else 1 for r in results)
            zipped: dict[str, Any] = {}
            for i in range(max_len):
                for j, r in enumerate(results):
                    if isinstance(r, dict):
                        keys = list(r.keys())
                        if i < len(keys):
                            zipped[f"source_{j}_{keys[i]}"] = r[keys[i]]
            return zipped

        if strategy == MergeStrategy.CHAIN:
            first = dict(results[0]) if results else {}
            for r in results[1:]:
                first.update(r)
            return first

        return {"results": results}  # type: ignore[unreachable]

    def _apply_mapping(
        self,
        data: dict[str, Any],
        mapping: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply a field mapping to the merged result.

        Args:
            data: The merged result dict.
            mapping: The field mapping (source_key -> target_key).

        Returns:
            The mapped result dict.
        """
        mapped = {}
        for source_key, target_key in mapping.items():
            mapped[target_key] = data.get(source_key)
        return mapped


__all__ = ["ApiComposer"]
