"""Memory summarization utilities."""

from __future__ import annotations

from eaip.memory.models import MemoryItem


class ExtractiveMemorySummarizer:
    """Deterministic summarizer that extracts concise memory snippets."""

    async def summarize(
        self,
        memories: list[MemoryItem],
        max_length: int = 500,
    ) -> str:
        """Summarize memory content into a bounded string."""
        if max_length <= 0 or not memories:
            return ""

        ordered = sorted(
            memories,
            key=lambda item: (item.importance, item.updated_at),
            reverse=True,
        )
        snippets: list[str] = []
        remaining = max_length
        for item in ordered:
            text = _normalize_space(item.content_summary or item.content)
            if not text:
                continue
            prefix = f"{item.memory_type.value}: "
            budget = remaining - len(prefix)
            if budget <= 0:
                break
            snippet = text[:budget].rstrip()
            snippets.append(f"{prefix}{snippet}")
            remaining = max_length - len(" ".join(snippets))
            if remaining <= 1:
                break
        return " ".join(snippets)[:max_length].rstrip()


def _normalize_space(value: str) -> str:
    return " ".join(value.split())


__all__ = ["ExtractiveMemorySummarizer"]
