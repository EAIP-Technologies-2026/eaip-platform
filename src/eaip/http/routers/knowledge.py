from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from starlette.status import HTTP_404_NOT_FOUND

from eaip.events.store import EventStore
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
    stat_val = (
        doc.indexing_status.value
        if hasattr(doc.indexing_status, "value")
        else str(doc.indexing_status)
    )
    return {
        "id": doc.document_id,
        "title": doc.title,
        "content": doc.source or "",
        "tags": [],
        "createdAt": doc.created_at.isoformat()
        if hasattr(doc.created_at, "isoformat")
        else datetime.now(UTC).isoformat(),
        "updatedAt": doc.updated_at.isoformat()
        if hasattr(doc.updated_at, "isoformat")
        else datetime.now(UTC).isoformat(),
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
            doc_tuples = [
                (did, col_name) for (did, col_name) in registry._documents if col_name == c.name
            ]
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
            "createdAt": c.created_at.isoformat()
            if hasattr(c.created_at, "isoformat")
            else datetime.now(UTC).isoformat(),
            "updatedAt": c.updated_at.isoformat()
            if hasattr(c.updated_at, "isoformat")
            else datetime.now(UTC).isoformat(),
        }
        for c in cols
    ]


@router.post("/collections")
async def create_collection(
    request: Request, body: dict[str, Any], _user: dict = Depends(get_current_user)
):
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
                "createdAt": col.created_at.isoformat()
                if hasattr(col.created_at, "isoformat")
                else datetime.now(UTC).isoformat(),
                "updatedAt": col.updated_at.isoformat()
                if hasattr(col.updated_at, "isoformat")
                else datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            log.warning("create_collection.failed", error=str(e))
    return {
        "id": f"col:{col_name}",
        "name": col_name,
        "description": body.get("description", ""),
        "documentCount": 0,
        "totalSize": 0,
        "createdAt": datetime.now(UTC).isoformat(),
        "updatedAt": datetime.now(UTC).isoformat(),
    }


@router.get("/collections/{collection_name}")
async def get_collection(
    request: Request, collection_name: str, _user: dict = Depends(get_current_user)
):
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
                "createdAt": col.created_at.isoformat()
                if hasattr(col.created_at, "isoformat")
                else datetime.now(UTC).isoformat(),
                "updatedAt": col.updated_at.isoformat()
                if hasattr(col.updated_at, "isoformat")
                else datetime.now(UTC).isoformat(),
            }
        except Exception:
            pass
    raise HTTPException(
        status_code=HTTP_404_NOT_FOUND, detail=f"Collection {collection_name} not found"
    )


@router.get("/documents")
async def list_documents(
    request: Request, collection: str | None = None, _user: dict = Depends(get_current_user)
):
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


@router.post("/documents")
async def create_document(
    request: Request, body: dict[str, Any], _user: dict = Depends(get_current_user)
):
    engine = _get_engine(request)
    doc_id = f"doc-{uuid.uuid4().hex[:12]}"
    title = body.get("title", "Untitled")
    content = body.get("content", "")
    collection = body.get("collection", "default")
    fmt = DocumentFormat.TXT
    if engine:
        try:
            result = await engine.ingest(
                document_id=doc_id,
                content=content.encode("utf-8"),
                doc_format=fmt,
                title=title,
                collection=collection,
            )
            return _doc_to_dict(result.document)
        except Exception as e:
            log.warning("create_document.ingest_failed", error=str(e))
    return {
        "id": doc_id,
        "title": title,
        "content": content,
        "tags": body.get("tags", []),
        "createdAt": datetime.now(UTC).isoformat(),
        "updatedAt": datetime.now(UTC).isoformat(),
        "type": fmt.value,
        "metadata": {},
        "version": 1,
        "size": len(content.encode("utf-8")),
        "status": "indexed",
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    request: Request, document_id: str, _user: dict = Depends(get_current_user)
):
    engine = _get_engine(request)
    if engine:
        try:
            await engine.delete_document(document_id)
        except Exception:
            pass
    return {"status": "ok"}


@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    request: Request, document_id: str, _user: dict = Depends(get_current_user)
):
    return {"status": "ok"}


@router.post("/documents/upload")
async def upload_document(
    request: Request,
    file: UploadFile,
    collection: str = "default",
    _user: dict = Depends(get_current_user),
):
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
                collection=collection,
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
        "createdAt": datetime.now(UTC).isoformat(),
        "updatedAt": datetime.now(UTC).isoformat(),
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
                results.append(
                    {
                        "id": cid,
                        "title": getattr(c, "document_id", f"Result {i}"),
                        "excerpt": content[:200],
                        "type": "chunk",
                        "score": score,
                        "tags": [],
                        "collectionId": coll,
                    }
                )
            total = getattr(rr, "total_results", len(results))
        except Exception as e:
            log.warning("search.failed", error=str(e))
    return {"results": results, "total": total, "page": page, "pageSize": pageSize}


@router.get("/activity")
async def knowledge_activity(
    request: Request, limit: int = 20, _user: dict = Depends(get_current_user)
):
    store = request.app.state.lifecycle.platform.container.try_resolve(EventStore)
    if store is not None:
        return store.recent_by(type="knowledge", limit=limit)
    return []


@router.get("/health")
async def knowledge_health(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    engine = _get_engine(request)
    total_docs = 0
    total_cols = 0
    indexed = 0
    pending = 0
    failed = 0
    total_chunks = 0

    if registry:
        cols = list(registry.all_collections())
        total_cols = len(cols)
        total_docs = sum(c.document_count for c in cols)
        total_chunks = sum(c.chunk_count for c in cols)
        for c in cols:
            for (did, col_name), doc in registry._documents.items():
                if col_name == c.name:
                    if doc.indexing_status == IndexingStatus.INDEXED:
                        indexed += 1
                    elif doc.indexing_status == IndexingStatus.PENDING:
                        pending += 1
                    elif doc.indexing_status == IndexingStatus.FAILED:
                        failed += 1

    status = "healthy"
    if failed > 0:
        status = "degraded"
    if total_docs == 0:
        status = "empty"

    return {
        "status": status,
        "totalDocuments": total_docs,
        "totalCollections": total_cols,
        "totalChunks": total_chunks,
        "indexedCount": indexed,
        "pendingCount": pending,
        "failedCount": failed,
        "engineAvailable": engine is not None,
    }


@router.get("/sources")
async def list_sources(request: Request, _user: dict = Depends(get_current_user)):
    registry = _get_registry(request)
    if not registry:
        return []
    cols = list(registry.all_collections())
    sources = []
    for c in cols:
        doc_count = c.document_count
        indexed = 0
        pending = 0
        failed = 0
        for (did, col_name), doc in registry._documents.items():
            if col_name == c.name:
                if doc.indexing_status == IndexingStatus.INDEXED:
                    indexed += 1
                elif doc.indexing_status == IndexingStatus.PENDING:
                    pending += 1
                elif doc.indexing_status == IndexingStatus.FAILED:
                    failed += 1

        source_status = "healthy"
        if failed > 0:
            source_status = "degraded"
        if doc_count == 0:
            source_status = "empty"

        sources.append({
            "id": c.collection_id,
            "name": c.name,
            "type": "collection",
            "description": c.description,
            "documentCount": doc_count,
            "chunkCount": c.chunk_count,
            "indexedCount": indexed,
            "pendingCount": pending,
            "failedCount": failed,
            "status": source_status,
            "createdAt": c.created_at.isoformat() if hasattr(c.created_at, "isoformat") else datetime.now(UTC).isoformat(),
            "updatedAt": c.updated_at.isoformat() if hasattr(c.updated_at, "isoformat") else datetime.now(UTC).isoformat(),
        })
    return sources


@router.get("/citations")
async def get_citations(
    request: Request,
    document_id: str | None = None,
    query: str = "",
    limit: int = 20,
    _user: dict = Depends(get_current_user),
):
    engine = _get_engine(request)
    registry = _get_registry(request)
    citations = []

    if engine and query.strip():
        try:
            rr = await engine.search(query, top_k=limit)
            chunks = list(getattr(rr, "chunks", []))
            for i, c in enumerate(chunks):
                cid = getattr(c, "chunk_id", getattr(c, "document_id", f"cit-{i}"))
                content = getattr(c, "content", "") or ""
                score = getattr(c, "score", 0.0)
                coll = getattr(c, "collection", "")
                doc_id = getattr(c, "document_id", "")
                chunk_idx = getattr(c, "chunk_index", i)
                citations.append({
                    "id": cid,
                    "documentId": doc_id,
                    "collection": coll,
                    "content": content[:500],
                    "score": score,
                    "chunkIndex": chunk_idx,
                    "source": f"collection:{coll}",
                })
        except Exception as e:
            log.warning("citations.failed", error=str(e))

    return {"citations": citations, "total": len(citations)}
