"""Document Intelligence Engine — provider-abstracted ingestion pipeline.

Pipeline stages (matching spec order):
  1. OCR           — provider.ocr(content)
  2. Layout        — from provider result ``layout``
  3. Classification — request classification or provider-derived
  4. Entity        — provider entities
  5. Table         — provider tables
  6. Provenance    — build provenance dict
  7. Knowledge ingest — via knowledge_engine.ingest if available

All storage is tenant-isolated (key = tenant_id:document_id).
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from eaip.document_intelligence.models import DocumentRecord, DocumentStatus
from eaip.document_intelligence.providers import PROVIDERS, LocalOCRProvider
from eaip.shared.time import utc_now
from eaip.logging.context import get_logger

log = get_logger("eaip.document_intelligence.engine")


class DocumentIntelligenceEngine:
    """Provider-abstracted document intelligence with optional Knowledge Engine feed."""

    def __init__(
        self,
        providers: dict[str, Any] | None = None,
        knowledge_engine: Any | None = None,
        event_bus: Any | None = None,
    ) -> None:
        self._providers: dict[str, Any] = providers if providers is not None else dict(PROVIDERS)
        # Ensure local always present as fallback
        if "local" not in self._providers:
            self._providers["local"] = LocalOCRProvider()
        self._knowledge_engine = knowledge_engine
        self._event_bus = event_bus
        # Tenant-isolated store: key = "tenant_id:document_id"
        self._store: dict[str, DocumentRecord] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _key(self, tenant_id: str, document_id: str) -> str:
        return f"{tenant_id}:{document_id}"

    def _resolve_provider(self, ocr_provider: str) -> tuple[str, Any]:
        provider = self._providers.get(ocr_provider)
        if provider is not None:
            return ocr_provider, provider
        # Fallback to local
        return "local", self._providers["local"]

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        try:
            result = self._event_bus.publish({"type": event_type, **payload})
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self,
        tenant_id: str,
        source: str,
        content: bytes,
        classification: str = "",
        ocr_provider: str = "local",
    ) -> DocumentRecord:
        """Ingest a document through the full pipeline.

        Args:
            tenant_id: Tenant scope.
            source: Source filename or URI.
            content: Raw file bytes.
            classification: Document classification label (optional, '' -> 'general').
            ocr_provider: Provider name to use (defaults to 'local').

        Returns:
            DocumentRecord in ``extracted`` (or ``failed``) status.
        """
        document_id = f"doc-{uuid.uuid4().hex[:12]}"
        provider_name, provider = self._resolve_provider(ocr_provider)

        now = utc_now()

        # Initial pending record
        record = DocumentRecord(
            document_id=document_id,
            tenant_id=tenant_id,
            source=source,
            status=DocumentStatus.processing,
            ocr_provider=provider_name,
            classification=classification or "general",
            created_at=now,
            updated_at=now,
        )
        # Persist pending before OCR so callers can observe processing
        self._store[self._key(tenant_id, document_id)] = record
        self._publish("document.processing", {"document_id": document_id, "tenant_id": tenant_id})

        try:
            # Stage 1: OCR / extraction
            ocr_result: dict[str, Any] = provider.ocr(content)

            # Stage 2: Layout (from provider)
            layout = ocr_result.get("layout", {})

            # Stage 3: Classification — honour caller-provided, else derive
            final_classification = classification or ocr_result.get("classification") or "general"

            # Stage 4 & 5: Entities / Tables
            entities_raw = ocr_result.get("entities", [])
            tables_raw = ocr_result.get("tables", [])
            confidence = float(ocr_result.get("confidence", 0.9))
            text = ocr_result.get("text", "")

            # Normalise to tuples of dicts
            extracted_entities: tuple[dict[str, Any], ...] = tuple(
                dict(e) if isinstance(e, dict) else {"text": str(e), "type": "entity"} for e in entities_raw
            )
            extracted_tables: tuple[dict[str, Any], ...] = tuple(
                dict(t) if isinstance(t, dict) else {"rows": [[str(t)]]} for t in tables_raw
            )

            # Stage 6: Provenance
            provenance: dict[str, Any] = {
                "source": source,
                "provider": provider_name,
                "bytes": len(content),
                "text_length": len(text),
                "layout": layout,
                "ingested_at": now.isoformat(),
                "ocr_confidence": confidence,
            }

            # Build extracted record
            record = DocumentRecord(
                document_id=document_id,
                tenant_id=tenant_id,
                source=source,
                status=DocumentStatus.extracted,
                ocr_provider=provider_name,
                classification=final_classification,
                extracted_entities=extracted_entities,
                extracted_tables=extracted_tables,
                confidence=confidence,
                provenance=provenance,
                validation={},
                error="",
                created_at=now,
                updated_at=utc_now(),
            )
            self._store[self._key(tenant_id, document_id)] = record
            self._publish("document.extracted", {"document_id": document_id, "tenant_id": tenant_id, "classification": final_classification})

            # Stage 7: Knowledge Engine ingest (best-effort, never fails the pipeline)
            if self._knowledge_engine is not None:
                try:
                    ke = self._knowledge_engine
                    # Prefer async ingest if available
                    ingest_fn = getattr(ke, "ingest", None)
                    if ingest_fn is not None:
                        # Detect if ingest is async
                        maybe_coro = ingest_fn(
                            document_id=document_id,
                            content=content,
                            doc_format="txt",
                            title=source or document_id,
                            collection=f"doc-intel-{tenant_id}",
                        )
                        if asyncio.iscoroutine(maybe_coro):
                            # Fire-and-forget for sync ingest path; try to schedule
                            try:
                                asyncio.create_task(maybe_coro)  # type: ignore[arg-type]
                            except RuntimeError:
                                # No running loop (sync context) — run briefly
                                pass
                    # Also update provenance to note knowledge ingest attempted
                    record = record.model_copy(update={"provenance": {**provenance, "knowledge_ingest": "attempted"}})
                    self._store[self._key(tenant_id, document_id)] = record
                except Exception as exc:  # noqa: BLE001
                    log.warning("document.knowledge_ingest.failed", document_id=document_id, error=str(exc))

            return self._store[self._key(tenant_id, document_id)]

        except Exception as exc:  # noqa: BLE001
            # Failure path
            error_record = DocumentRecord(
                document_id=document_id,
                tenant_id=tenant_id,
                source=source,
                status=DocumentStatus.failed,
                ocr_provider=provider_name,
                classification=classification or "general",
                extracted_entities=(),
                extracted_tables=(),
                confidence=0.0,
                provenance={"source": source, "provider": provider_name, "error": str(exc)},
                validation={},
                error=str(exc),
                created_at=now,
                updated_at=utc_now(),
            )
            self._store[self._key(tenant_id, document_id)] = error_record
            self._publish("document.failed", {"document_id": document_id, "tenant_id": tenant_id, "error": str(exc)})
            return error_record

    def get(self, document_id: str, tenant_id: str) -> DocumentRecord | None:
        """Return a single document record (tenant-scoped)."""
        return self._store.get(self._key(tenant_id, document_id))

    def list_for_tenant(self, tenant_id: str) -> list[DocumentRecord]:
        """List all documents for a tenant."""
        prefix = f"{tenant_id}:"
        return [v for k, v in self._store.items() if k.startswith(prefix)]

    def validate(
        self,
        document_id: str,
        tenant_id: str,
        corrections: dict[str, Any],
    ) -> DocumentRecord | None:
        """Apply human corrections and mark document as validated.

        Args:
            document_id: Document to validate.
            tenant_id: Tenant scope.
            corrections: Dict of corrections (e.g. ``{entities: [...], tables: [...]}``).

        Returns:
            Updated DocumentRecord or None if not found / wrong tenant.
        """
        rec = self.get(document_id, tenant_id)
        if rec is None:
            return None

        # Allow corrections to override entities / tables / classification
        new_entities = rec.extracted_entities
        new_tables = rec.extracted_tables
        new_classification = rec.classification

        if isinstance(corrections, dict):
            if "entities" in corrections and isinstance(corrections["entities"], list):
                new_entities = tuple(
                    dict(e) if isinstance(e, dict) else {"text": str(e), "type": "entity"} for e in corrections["entities"]
                )
            if "tables" in corrections and isinstance(corrections["tables"], list):
                new_tables = tuple(
                    dict(t) if isinstance(t, dict) else {"rows": [[str(t)]]} for t in corrections["tables"]
                )
            if "classification" in corrections:
                new_classification = str(corrections["classification"])

        # Merge corrections into validation dict for audit
        merged_validation: dict[str, Any] = {**rec.validation, **corrections, "validated_at": utc_now().isoformat()}

        updated = rec.model_copy(
            update={
                "status": DocumentStatus.validated,
                "classification": new_classification,
                "extracted_entities": new_entities,
                "extracted_tables": new_tables,
                "validation": merged_validation,
                "error": "",
                "updated_at": utc_now(),
            }
        )
        self._store[self._key(tenant_id, document_id)] = updated
        self._publish("document.validated", {"document_id": document_id, "tenant_id": tenant_id})
        return updated

    def get_entities(self, document_id: str, tenant_id: str) -> list[dict[str, Any]] | None:
        """Return extracted entities for a document, or None if not found."""
        rec = self.get(document_id, tenant_id)
        if rec is None:
            return None
        return list(rec.extracted_entities)

    def get_tables(self, document_id: str, tenant_id: str) -> list[dict[str, Any]] | None:
        """Return extracted tables for a document, or None if not found."""
        rec = self.get(document_id, tenant_id)
        if rec is None:
            return None
        return list(rec.extracted_tables)
