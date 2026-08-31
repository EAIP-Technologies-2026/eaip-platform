"""Document Intelligence models — DocumentRecord and OCRProvider Protocol.

Provider-abstracted document intelligence that feeds the Knowledge Engine.
All records are tenant-isolated and immutable (frozen).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from eaip.shared.time import utc_now


class DocumentStatus(StrEnum):
    """Lifecycle status of a document through the intelligence pipeline."""

    pending = "pending"
    processing = "processing"
    extracted = "extracted"
    validated = "validated"
    failed = "failed"


@runtime_checkable
class OCRProvider(Protocol):
    """Provider interface for OCR / extraction.

    Implementations must be deterministic for tests and interchangeable
    for production providers. The result dict should contain at minimum
    ``entities``, ``tables``, ``confidence`` and ``text`` keys.
    """

    def ocr(self, content: bytes) -> dict[str, Any]:
        """Run OCR / layout / entity extraction on raw bytes.

        Args:
            content: Raw file bytes (PDF, image, txt, etc.).

        Returns:
            Dict with keys ``entities`` (list[dict]), ``tables`` (list[dict]),
            ``confidence`` (float), ``text`` (str).
        """
        ...


class DocumentRecord(BaseModel):
    """Immutable record produced by the Document Intelligence pipeline."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str
    tenant_id: str
    source: str = ""
    version: str = "1.0.0"
    status: DocumentStatus = DocumentStatus.pending
    ocr_provider: str = "local"
    classification: str = ""
    extracted_entities: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    extracted_tables: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    confidence: float = 0.0
    provenance: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


__all__ = ["DocumentRecord", "DocumentStatus", "OCRProvider"]
