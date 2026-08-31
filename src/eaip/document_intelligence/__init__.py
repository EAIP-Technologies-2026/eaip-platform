"""Document Intelligence — provider-abstracted document understanding that feeds the Knowledge Engine."""

from __future__ import annotations

from eaip.document_intelligence.engine import DocumentIntelligenceEngine
from eaip.document_intelligence.models import DocumentRecord, DocumentStatus, OCRProvider
from eaip.document_intelligence.providers import (
    LocalOCRProvider,
    OCR_PROVIDERS,
    PROVIDERS,
    get_provider,
    list_providers,
    register_provider,
)

__all__ = [
    "DocumentIntelligenceEngine",
    "DocumentRecord",
    "DocumentStatus",
    "LocalOCRProvider",
    "OCR_PROVIDERS",
    "OCRProvider",
    "PROVIDERS",
    "get_provider",
    "list_providers",
    "register_provider",
]
