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


class SlidingWindowTokenCompressor:
    """Compresses chat messages down to fit within a target token window."""

    def __init__(self, target_max_tokens: int = 1000) -> None:
        self.target_max_tokens = target_max_tokens

    def compress_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        if not messages:
            return []
        
        system_msgs = [m for m in messages if m.get("role") == "system"]
        chat_msgs = [m for m in messages if m.get("role") != "system"]

        # Approximate token count (1 token ~= 4 characters)
        budget_chars = self.target_max_tokens * 4
        current_chars = sum(len(m.get("content", "")) for m in system_msgs)

        retained_chat: list[dict[str, str]] = []
        for m in reversed(chat_msgs):
            content_len = len(m.get("content", ""))
            if current_chars + content_len <= budget_chars or not retained_chat:
                retained_chat.insert(0, m)
                current_chars += content_len
            else:
                break

        return system_msgs + retained_chat


def _normalize_space(value: str) -> str:
    return " ".join(value.split())


__all__ = ["ExtractiveMemorySummarizer", "SlidingWindowTokenCompressor"]

