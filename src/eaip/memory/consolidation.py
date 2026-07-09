"""Memory consolidation — summarization, deduplication, and type promotion."""

from __future__ import annotations

import time
from typing import Any, Protocol

from eaip.logging.context import get_logger
from eaip.memory.exceptions import MemoryConsolidationError
from eaip.memory.models import (
    ConsolidationConfig,
    ConsolidationReport,
    MemoryItem,
)


class ConsolidationStrategy(Protocol):
    """Protocol for memory consolidation strategies."""

    async def should_consolidate(
        self,
        memories: list[MemoryItem],
        config: ConsolidationConfig,
    ) -> bool:
        """Determine if a set of memories should be consolidated.

        Args:
            memories: The memories to evaluate.
            config: The consolidation configuration.

        Returns:
            True if consolidation should proceed.
        """
        ...

    async def consolidate(
        self,
        memories: list[MemoryItem],
        config: ConsolidationConfig,
    ) -> ConsolidationReport:
        """Consolidate a set of memories.

        Args:
            memories: The memories to consolidate.
            config: The consolidation configuration.

        Returns:
            A ConsolidationReport with results.
        """
        ...


class TimeBasedConsolidationStrategy:
    """Consolidates memories that have existed beyond a time threshold."""

    async def should_consolidate(
        self,
        memories: list[MemoryItem],
        config: ConsolidationConfig,
    ) -> bool:
        """Check if enough memories exist for consolidation.

        Args:
            memories: The memories to evaluate.
            config: The consolidation configuration.

        Returns:
            True if enough memories exist.
        """
        return len(memories) >= config.min_memories_for_consolidation

    async def consolidate(
        self,
        memories: list[MemoryItem],
        _config: ConsolidationConfig,
    ) -> ConsolidationReport:
        """Produce a report indicating consolidation is needed.

        Args:
            memories: The memories to consolidate.

        Returns:
            A report noting consolidate-ready memories.
        """
        return ConsolidationReport(
            source_count=len(memories),
            consolidated_count=0,
            removed_count=0,
            summaries_generated=0,
            duration_ms=0.0,
            details={"ready": True, "strategy": "time_based"},
        )


class NeverConsolidateStrategy:
    """Consolidation strategy that never triggers."""

    async def should_consolidate(
        self,
        _memories: list[MemoryItem],
        _config: ConsolidationConfig,
    ) -> bool:
        """Always return False.

        Returns:
            Always False.
        """
        return False

    async def consolidate(
        self,
        _memories: list[MemoryItem],
        _config: ConsolidationConfig,
    ) -> ConsolidationReport:
        """Return an empty report.

        Returns:
            An empty report.
        """
        return ConsolidationReport()


class ConditionalConsolidationStrategy:
    """Consolidation strategy with custom condition and action callables."""

    def __init__(
        self,
        condition: Any = None,
        action: Any = None,
    ) -> None:
        """Initialize the strategy.

        Args:
            condition: Optional callable(memories, config) -> bool.
            action: Optional callable(memories, config) -> ConsolidationReport.
        """
        self._condition = condition
        self._action = action

    async def should_consolidate(
        self,
        memories: list[MemoryItem],
        config: ConsolidationConfig,
    ) -> bool:
        """Evaluate the condition.

        Args:
            memories: The memories to evaluate.
            config: The consolidation configuration.

        Returns:
            True if consolidation should proceed.
        """
        if self._condition:
            return self._condition(memories, config)
        return len(memories) >= config.min_memories_for_consolidation

    async def consolidate(
        self,
        memories: list[MemoryItem],
        config: ConsolidationConfig,
    ) -> ConsolidationReport:
        """Execute the consolidation action.

        Args:
            memories: The memories to consolidate.
            config: The consolidation configuration.

        Returns:
            A ConsolidationReport with results.
        """
        if self._action:
            return self._action(memories, config)
        return ConsolidationReport(
            source_count=len(memories),
            consolidated_count=0,
            removed_count=0,
            summaries_generated=0,
        )


class MemoryConsolidationService:
    """Service for consolidating memories.

    Handles episodic-to-semantic promotion, deduplication,
    and summarization orchestration.
    """

    def __init__(
        self,
        config: ConsolidationConfig | None = None,
        strategy: ConsolidationStrategy | None = None,
    ) -> None:
        """Initialize the consolidation service.

        Args:
            config: Optional consolidation configuration.
            strategy: Optional consolidation strategy.
        """
        self._config = config or ConsolidationConfig()
        self._strategy = strategy or TimeBasedConsolidationStrategy()
        self._log = get_logger("eaip.memory.consolidation")

    async def consolidate_episodic_to_semantic(
        self,
        episodic_memories: list[MemoryItem],
    ) -> ConsolidationReport:
        """Consolidate episodic memories into a semantic memory.

        Args:
            episodic_memories: The episodic memories to consolidate.

        Returns:
            A ConsolidationReport with results.

        Raises:
            MemoryConsolidationError: If consolidation fails.
        """
        t0 = time.monotonic()
        if not episodic_memories:
            return ConsolidationReport()

        try:
            should = await self._strategy.should_consolidate(
                episodic_memories, self._config
            )
            if not should:
                return ConsolidationReport(source_count=len(episodic_memories))

            combined_content = " ".join(m.content for m in episodic_memories)
            combined_tags: set[str] = set()
            for m in episodic_memories:
                combined_tags.update(m.tags)

            report = ConsolidationReport(
                source_count=len(episodic_memories),
                consolidated_count=1,
                removed_count=0,
                summaries_generated=1,
                duration_ms=(time.monotonic() - t0) * 1000,
                details={
                    "combined_length": len(combined_content),
                    "combined_tags": list(combined_tags),
                },
            )
            self._log.info(
                "consolidation.episodic_to_semantic",
                source_count=len(episodic_memories),
                duration_ms=round(report.duration_ms, 2),
            )
            return report
        except MemoryConsolidationError:
            raise
        except Exception as exc:
            raise MemoryConsolidationError(
                f"Episodic-to-semantic consolidation failed: {exc}",
            ) from exc

    async def deduplicate(
        self,
        memories: list[MemoryItem],
    ) -> tuple[list[MemoryItem], list[MemoryItem]]:
        """Remove duplicate memories based on content hash.

        Args:
            memories: The memories to deduplicate.

        Returns:
            A tuple of (unique_memories, duplicates).
        """
        seen: set[str] = set()
        unique: list[MemoryItem] = []
        duplicates: list[MemoryItem] = []
        for m in memories:
            content_hash = hash(m.content)
            if content_hash in seen:
                duplicates.append(m)
            else:
                seen.add(content_hash)
                unique.append(m)
        if duplicates:
            self._log.debug("consolidation.dedup", removed=len(duplicates))
        return unique, duplicates


__all__ = [
    "ConditionalConsolidationStrategy",
    "ConsolidationStrategy",
    "MemoryConsolidationService",
    "NeverConsolidateStrategy",
    "TimeBasedConsolidationStrategy",
]
