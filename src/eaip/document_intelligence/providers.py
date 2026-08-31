"""Document Intelligence providers — OCRProvider interface and registry.

Provider-abstracted OCR extraction. Production providers can be swapped
via the registry without changing the engine.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class OCRProvider(Protocol):
    """OCR provider interface.

    Implementations receive raw bytes and return a deterministic dict
    with ``entities``, ``tables``, ``confidence`` and ``text``.
    """

    def ocr(self, content: bytes) -> dict[str, Any]:
        """Extract entities/tables from raw bytes."""
        ...


class LocalOCRProvider:
    """Deterministic fake OCR — no external dependencies.

    Splits decoded text into word-level entities and synthesises a
    single table with confidence 0.9. Fully deterministic for tests.
    """

    name: str = "local"

    def ocr(self, content: bytes) -> dict[str, Any]:  # noqa: D102
        text = content.decode("utf-8", errors="replace")
        # Preserve original text for knowledge ingest provenance
        stripped = text.strip()
        if not stripped:
            return {
                "text": text,
                "entities": [],
                "tables": [],
                "confidence": 0.9,
                "layout": {"blocks": []},
            }

        # Deterministic word tokenisation — split on whitespace
        words = stripped.split()

        # Entities: each word as an entity with type "entity"
        # Use "WORD" type variant for slightly richer output
        entities: list[dict[str, Any]] = [
            {"text": w, "type": "entity", "confidence": 0.9} for w in words
        ]

        # Tables: one table with a single row containing up to first 5 words
        # If content contains tabular hints (|, comma, tab) produce 2 rows
        tables: list[dict[str, Any]]
        if any(sep in text for sep in ("|", "\n")):
            # Build rows by splitting lines, then cells by | or comma
            rows: list[list[str]] = []
            for line in stripped.splitlines():
                line = line.strip()
                if not line:
                    continue
                if "|" in line:
                    cells = [c.strip() for c in line.split("|") if c.strip()]
                elif "," in line:
                    cells = [c.strip() for c in line.split(",") if c.strip()]
                else:
                    cells = [line]
                if cells:
                    rows.append(cells)
                if len(rows) >= 5:
                    break
            if not rows:
                rows = [[w for w in words[:5]]]
            tables = [{"rows": rows, "confidence": 0.9}]
        else:
            # Single row table from first words
            tables = [{"rows": [[w for w in words[:5]]], "confidence": 0.9}]

        # Layout: simple block structure
        layout = {
            "blocks": [{"type": "paragraph", "text": line} for line in stripped.splitlines() if line.strip()],
            "page_count": 1,
        }

        return {
            "text": text,
            "entities": entities,
            "tables": tables,
            "confidence": 0.9,
            "layout": layout,
        }


# -----------------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------------

PROVIDERS: dict[str, OCRProvider] = {
    "local": LocalOCRProvider(),
}

# Alias for backwards compatibility with spec wording
OCR_PROVIDERS: dict[str, OCRProvider] = PROVIDERS


def register_provider(name: str, provider: OCRProvider) -> None:
    """Register (or replace) an OCR provider by name."""
    PROVIDERS[name] = provider
    OCR_PROVIDERS[name] = provider


def get_provider(name: str = "local") -> OCRProvider:
    """Return provider by name, falling back to ``local``."""
    provider = PROVIDERS.get(name)
    if provider is not None:
        return provider
    # Fallback to local if unknown name requested
    return PROVIDERS["local"]


def list_providers() -> list[str]:
    """List registered provider names."""
    return list(PROVIDERS.keys())


__all__ = ["LocalOCRProvider", "OCR_PROVIDERS", "OCRProvider", "PROVIDERS", "get_provider", "list_providers", "register_provider"]
