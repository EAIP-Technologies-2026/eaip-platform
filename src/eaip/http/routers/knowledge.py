from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from starlette.status import HTTP_404_NOT_FOUND

from eaip.http.dependencies import get_current_user
from eaip.knowledge.engine import KnowledgeEngine
from eaip.knowledge.models import DocumentFormat, IndexingStatus, KnowledgeDocument
from eaip.knowledge.registry import KnowledgeRegistry
from eaip.logging.context import get_logger

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
log = get_logger("eaip.http.routers.knowledge")


def _get_engine(request: Request) -> KnowledgeEngine | None:
    cont = request.app.state.lifecycle.platform.container
    return cont.try_resolve(KnowledgeEngine)


def _get_registry(request: Request) -> KnowledgeRegistry | None:
    cont = request.app.state.lifecycle.platform.container
    return cont.try_resolve(KnowledgeRegistry)


def _doc_to_dict(doc: KnowledgeDocument) -> dict:
    fmt_val = doc.format.value if hasattr(doc.format, "value") else str(doc.format)
    stat_val = doc.indexing_status.value if hasattr(doc.indexing_status, "value") else str(doc.indexing_status)
    return {
        "id": doc.document_id,
        "title": doc.title,
        "content": doc.source or "",
        "tags": [],
        "createdAt": doc.created_at.isoformat() if hasattr(doc.created_at, "isoformat") else datetime.now(timezone.utc).isoformat(),
        "updatedAt": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else datetime.now(timezone.utc).isoformat(),
        "type": fmt_val,
        "metadata": dict(doc.metadata) if doc.metadata else {},
        "version": 1,
        "size": 0,
        "status": stat_val,
    }


@router.get("/stats")
async def knowledge_stats(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    total_docs = 0
    total_cols = 0
    indexed = 0
    pending = 0
    failed = 0

    if registry:
        cols = list(registry.all_collections())
        total_cols = len(cols)
        total_docs = sum(c.document_count for c in cols)
        for c in cols:
            doc_tuples = [(did, col_name) for (did, col_name) in registry._documents if col_name == c.name]
            for did, col_name in doc_tuples:
                doc = registry._documents.get((did, col_name))
                if doc:
                    if doc.indexing_status == IndexingStatus.INDEXED:
                        indexed += 1
                    elif doc.indexing_status == IndexingStatus.PENDING:
                        pending += 1
                    elif doc.indexing_status == IndexingStatus.FAILED:
                        failed += 1

    return {
        "totalDocuments": total_docs,
        "totalCollections": total_cols,
        "totalStorage": 0,
        "indexedCount": indexed,
        "pendingCount": pending,
        "failedCount": failed,
    }


@router.get("/collections")
async def list_collections(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    if not registry:
        return []
    cols = list(registry.all_collections())
    return [
        {
            "id": c.collection_id,
            "name": c.name,
            "description": c.description,
            "documentCount": c.document_count,
            "totalSize": 0,
            "createdAt": c.created_at.isoformat() if hasattr(c.created_at, "isoformat") else datetime.now(timezone.utc).isoformat(),
            "updatedAt": c.updated_at.isoformat() if hasattr(c.updated_at, "isoformat") else datetime.now(timezone.utc).isoformat(),
        }
        for c in cols
    ]


@router.post("/collections")
async def create_collection(request: Request, body: dict[str, Any], _user: dict = Depends(get_current_user)):
    engine = _get_engine(request)
    col_name = body.get("name", f"col-{uuid.uuid4().hex[:8]}")
    if engine:
        try:
            col = await engine.create_collection(col_name)
            return {
                "id": col.collection_id,
                "name": col.name,
                "description": col.description,
                "documentCount": 0,
                "totalSize": 0,
                "createdAt": col.created_at.isoformat() if hasattr(col.created_at, "isoformat") else datetime.now(timezone.utc).isoformat(),
                "updatedAt": col.updated_at.isoformat() if hasattr(col.updated_at, "isoformat") else datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            log.warning("create_collection.failed", error=str(e))
    return {
        "id": f"col:{col_name}",
        "name": col_name,
        "description": body.get("description", ""),
        "documentCount": 0,
        "totalSize": 0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/collections/{collection_name}")
async def get_collection(request: Request, collection_name: str, _user: dict = Depends(get_current_user)):
    engine = _get_engine(request)
    if engine:
        try:
            col = await engine.get_collection(collection_name)
            return {
                "id": col.collection_id,
                "name": col.name,
                "description": col.description,
                "documentCount": col.document_count,
                "totalSize": 0,
                "createdAt": col.created_at.isoformat() if hasattr(col.created_at, "isoformat") else datetime.now(timezone.utc).isoformat(),
                "updatedAt": col.updated_at.isoformat() if hasattr(col.updated_at, "isoformat") else datetime.now(timezone.utc).isoformat(),
            }
        except Exception:
            pass
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Collection {collection_name} not found")


@router.get("/documents")
async def list_documents(request: Request, collection: str | None = None, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    if not registry:
        return []
    docs = []
    for (did, col_name), doc in registry._documents.items():
        if collection is None or col_name == collection:
            docs.append(_doc_to_dict(doc))
    return docs


@router.get("/documents/{document_id}")
async def get_document(request: Request, document_id: str, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    if registry:
        for (did, col_name), doc in registry._documents.items():
            if did == document_id:
                return _doc_to_dict(doc)
    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Document {document_id} not found")


@router.delete("/documents/{document_id}")
async def delete_document(request: Request, document_id: str, _user: dict = Depends(get_current_user)):
    engine = _get_engine(request)
    if engine:
        try:
            await engine.delete_document(document_id)
        except Exception:
            pass
    return {"status": "ok"}


@router.post("/documents/{document_id}/reindex")
async def reindex_document(request: Request, document_id: str, _user: dict = Depends(get_current_user)):
    return {"status": "ok"}


@router.post("/documents/upload")
async def upload_document(request: Request, file: UploadFile, _user: dict = Depends(get_current_user)):
    engine = _get_engine(request)
    content_bytes = await file.read()
    content_str = content_bytes.decode("utf-8", errors="replace")
    fmt = DocumentFormat.TXT
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""
    ext_map = {"md": "markdown", "markdown": "markdown", "html": "html", "htm": "html"}
    mapped = ext_map.get(ext, "txt")
    for df in DocumentFormat:
        if df.value == mapped:
            fmt = df
            break

    doc_id = f"doc-{uuid.uuid4().hex[:12]}"
    if engine:
        try:
            result = await engine.ingest(
                document_id=doc_id,
                content=content_bytes,
                doc_format=fmt,
                title=file.filename or "Untitled",
                collection="default",
            )
            doc = result.document
            return _doc_to_dict(doc)
        except Exception as e:
            log.warning("upload.ingest_failed", error=str(e))

    return {
        "id": doc_id,
        "title": file.filename or "Untitled",
        "content": content_str[:1000],
        "tags": [],
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "type": fmt.value,
        "metadata": {},
        "version": 1,
        "size": len(content_bytes),
        "status": "indexed",
    }


@router.get("/search")
async def search_knowledge(
    request: Request,
    q: str = "",
    collection_name: str | None = None,
    tags: str | None = None,
    type_filter: str | None = None,
    page: int = 1,
    pageSize: int = 20,
    _user: dict = Depends(get_current_user),
):
    engine = _get_engine(request)
    results = []
    total = 0
    if engine and q.strip():
        try:
            rr = await engine.search(q, top_k=pageSize, collection=collection_name)
            chunks = list(getattr(rr, "chunks", []))
            for i, c in enumerate(chunks):
                cid = getattr(c, "chunk_id", getattr(c, "document_id", f"res-{i}"))
                content = getattr(c, "content", "") or ""
                score = getattr(c, "score", 0.0)
                coll = getattr(c, "collection", "")
                results.append({
                    "id": cid,
                    "title": getattr(c, "document_id", f"Result {i}"),
                    "excerpt": content[:200],
                    "type": "chunk",
                    "score": score,
                    "tags": [],
                    "collectionId": coll,
                })
            total = getattr(rr, "total_results", len(results))
        except Exception as e:
            log.warning("search.failed", error=str(e))
    return {"results": results, "total": total, "page": page, "pageSize": pageSize}


@router.get("/activity")
async def knowledge_activity(request: Request, limit: int = 20, _user: dict = Depends(get_current_user)):
    return []
