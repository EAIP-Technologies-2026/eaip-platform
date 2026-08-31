"""Document Intelligence HTTP router — provider-abstracted document ingestion.

Prefix: /documents/intelligence  tags: documents-intelligence
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File

from eaip.http.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/documents/intelligence", tags=["documents-intelligence"])


def _engine(request: Request):  # type: ignore[no-untyped-def]
    from eaip.document_intelligence.engine import DocumentIntelligenceEngine

    eng = request.app.state.lifecycle.platform.container.try_resolve(DocumentIntelligenceEngine)
    if eng is None:
        # Try to wire optional knowledge engine if available
        ke = None
        try:
            from eaip.knowledge.engine import KnowledgeEngine  # noqa: PLC0415

            ke = request.app.state.lifecycle.platform.container.try_resolve(KnowledgeEngine)
        except Exception:
            ke = None
        eng = DocumentIntelligenceEngine(knowledge_engine=ke)
        request.app.state.lifecycle.platform.container.register_instance(DocumentIntelligenceEngine, eng)
    return eng


# Important: /list must be registered BEFORE /{document_id} to avoid path conflict
@router.get("/list")
async def list_documents(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    eng = _engine(request)
    records = eng.list_for_tenant(tenant_id)
    return [r.model_dump(mode="json") for r in records]


@router.post("/ingest")
async def ingest_document(
    request: Request,
    file: UploadFile | None = File(default=None),
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Ingest a document via UploadFile (multipart) or JSON body.

    Multipart: send ``file`` field with the document bytes. Optional form fields
    ``source``, ``classification``, ``ocr_provider`` are read if present.

    JSON: body ``{source, content, classification, ocr_provider}`` where
    ``content`` is a string (UTF-8 text). Binary can be base64-encoded and
    sent as ``content_base64`` as alternative.
    """
    eng = _engine(request)
    content_type = request.headers.get("content-type", "")

    source = ""
    content_bytes: bytes | None = None
    classification = ""
    ocr_provider = "local"

    # Case 1: multipart file upload (file provided via File param)
    if file is not None and file.filename:
        content_bytes = await file.read()
        source = file.filename or "upload"
        # Also try to read additional form fields if sent alongside file
        try:
            form = await request.form()
            if "source" in form and form["source"]:
                source = str(form["source"])
            if "classification" in form and form["classification"]:
                classification = str(form["classification"])
            if "ocr_provider" in form and form["ocr_provider"]:
                ocr_provider = str(form["ocr_provider"])
        except Exception:
            pass
    # Case 2: multipart without File param binding — parse form manually
    elif "multipart/form-data" in content_type:
        try:
            form = await request.form()
            # file may be under 'file', 'upload', or 'content'
            for key in ("file", "upload", "content", "document"):
                if key in form:
                    val = form[key]
                    # UploadFile
                    if hasattr(val, "read"):
                        content_bytes = await val.read()  # type: ignore[union-attr]
                        source = getattr(val, "filename", "") or source or key
                        break
                    elif isinstance(val, str) and val:
                        content_bytes = val.encode("utf-8")
                        source = key
                        break
            if "source" in form and form["source"]:
                source = str(form["source"])
            if "classification" in form and form["classification"]:
                classification = str(form["classification"])
            if "ocr_provider" in form and form["ocr_provider"]:
                ocr_provider = str(form["ocr_provider"])
        except Exception:
            pass

    # Case 3: JSON body
    if content_bytes is None:
        try:
            body: dict[str, Any] = await request.json()
        except Exception:
            body = {}
        # Support both raw string content and structured payload
        if body:
            source = str(body.get("source") or body.get("filename") or source or "json-content")
            classification = str(body.get("classification") or classification or "")
            ocr_provider = str(body.get("ocr_provider") or body.get("ocrProvider") or ocr_provider or "local")
            if "content_base64" in body and body["content_base64"]:
                import base64

                try:
                    content_bytes = base64.b64decode(str(body["content_base64"]))
                except Exception as exc:
                    raise HTTPException(status_code=400, detail=f"invalid content_base64: {exc}") from exc
            elif "content" in body:
                raw = body["content"]
                if isinstance(raw, bytes):
                    content_bytes = raw
                elif isinstance(raw, str):
                    content_bytes = raw.encode("utf-8")
                elif raw is not None:
                    content_bytes = json.dumps(raw).encode("utf-8")
            elif "text" in body and isinstance(body["text"], str):
                content_bytes = body["text"].encode("utf-8")
                source = str(body.get("source") or source or "json-text")

    if content_bytes is None:
        raise HTTPException(status_code=400, detail="No document content provided. Send multipart file or JSON {content}")

    # Ingest through engine (synchronous)
    try:
        record = eng.ingest(
            tenant_id=tenant_id,
            source=source,
            content=content_bytes,
            classification=classification,
            ocr_provider=ocr_provider,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return record.model_dump(mode="json")


@router.get("/{document_id}")
async def get_document(
    request: Request,
    document_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    eng = _engine(request)
    rec = eng.get(document_id, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="document not found")
    return rec.model_dump(mode="json")


@router.get("/{document_id}/entities")
async def get_entities(
    request: Request,
    document_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    eng = _engine(request)
    entities = eng.get_entities(document_id, tenant_id)
    if entities is None:
        raise HTTPException(status_code=404, detail="document not found")
    return {"document_id": document_id, "tenant_id": tenant_id, "entities": entities, "count": len(entities)}


@router.get("/{document_id}/tables")
async def get_tables(
    request: Request,
    document_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    eng = _engine(request)
    tables = eng.get_tables(document_id, tenant_id)
    if tables is None:
        raise HTTPException(status_code=404, detail="document not found")
    return {"document_id": document_id, "tenant_id": tenant_id, "tables": tables, "count": len(tables)}


@router.post("/{document_id}/validate")
async def validate_document(
    request: Request,
    document_id: str,
    tenant_id: str = Depends(get_tenant_id),
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    eng = _engine(request)
    try:
        body: dict[str, Any] = await request.json()
    except Exception:
        body = {}
    # Support both {corrections: {...}} and flat dict
    corrections = body.get("corrections") if isinstance(body.get("corrections"), dict) else body
    if not isinstance(corrections, dict):
        corrections = {}
    rec = eng.validate(document_id, tenant_id, corrections)
    if not rec:
        raise HTTPException(status_code=404, detail="document not found")
    return rec.model_dump(mode="json")
