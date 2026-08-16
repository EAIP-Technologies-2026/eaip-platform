"""SQL-backed memory store — persists MemoryItems to PostgreSQL via asyncpg.

Implements the full ``MemoryStore`` protocol (and ``archive_many``) so it can
drop in as a drop-in replacement for ``InMemoryStore`` when a PostgreSQL
connection is available.  All queries are tenant-scoped: the ``tenant_id``
column is always part of the WHERE clause, preventing cross-tenant access.
"""

from __future__ import annotations

import json
from typing import Any

from eaip.infrastructure.db.connection import DatabaseConnection
from eaip.logging.context import get_logger
from eaip.memory.base import MemoryStore
from eaip.memory.exceptions import MemoryNotFoundError, MemoryValidationError
from eaip.memory.models import (
    MemoryDomain,
    MemoryItem,
    MemoryQuery,
    MemoryScope,
    MemorySensitivity,
    MemoryStatus,
    MemorySearchResult,
    MemoryType,
    ScopedMemoryId,
)


def _fq_id(tenant_id: str, user_id: str | None, session_id: str | None,
           app_id: str | None, memory_id: str) -> str:
    parts = [tenant_id]
    if user_id:
        parts.append(user_id)
    if session_id:
        parts.append(session_id)
    if app_id:
        parts.append(app_id)
    return f"{':'.join(parts)}:{memory_id}"


def _parse_fq_id(fq_id: str) -> tuple[str, str | None, str | None, str | None, str]:
    parts = fq_id.split(":")
    memory_id = parts[-1]
    tenant_id = parts[0]
    middle = parts[1:-1] if len(parts) > 2 else []
    user_id = middle[0] if len(middle) >= 1 else None
    session_id = middle[1] if len(middle) >= 2 else None
    application_id = middle[2] if len(middle) >= 3 else None
    return tenant_id, user_id, session_id, application_id, memory_id


def _to_json_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else [parsed]
        except (TypeError, ValueError):
            return [val]
    return [val]


def _to_json_dict(val: Any) -> dict:
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}
    return {}


def _to_tuple_of_floats(val: Any) -> tuple[float, ...]:
    if val is None:
        return ()
    if isinstance(val, (list, tuple)):
        return tuple(float(v) for v in val if v is not None)
    if isinstance(val, str):
        try:
            return tuple(float(v) for v in json.loads(val))
        except (TypeError, ValueError):
            return ()
    return ()


def _deserialize_item(row: Any) -> MemoryItem:
    related_ids = _to_json_list(row["related_ids"])
    tags = _to_json_list(row["tags"])
    metadata = _to_json_dict(row["metadata"])
    embedding = _to_tuple_of_floats(row["embedding"])

    scope = MemoryScope(
        tenant_id=row["tenant_id"],
        user_id=row["user_id"],
        session_id=row["session_id"],
        application_id=row["application_id"],
    )
    return MemoryItem(
        memory_id=row["memory_id"],
        memory_type=MemoryType(row["memory_type"]),
        scope=scope,
        domain=MemoryDomain(row["domain"]),
        content=row["content"],
        content_summary=row["content_summary"] or "",
        importance=float(row["importance"]),
        confidence=float(row["confidence"]),
        sensitivity=MemorySensitivity(row["sensitivity"]),
        source=row["source"],
        provenance=row["provenance"],
        retention_policy=row["retention_policy"],
        status=MemoryStatus(row["status"]),
        parent_id=row["parent_id"],
        related_ids=tuple(related_ids),
        tags=tuple(tags),
        metadata=metadata,
        embedding=embedding,
        version=int(row["version"]),
        access_count=int(row["access_count"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        accessed_at=row["accessed_at"],
        expires_at=row["expires_at"],
    )


class SqlMemoryStore(MemoryStore):
    """PostgreSQL-backed :class:`MemoryStore` implementation.

    All operations are tenant-isolated — the ``tenant_id`` from the
    :class:`MemoryScope` is always included in SQL filters.
    """

    def __init__(self) -> None:
        self._log = get_logger("eaip.memory.store.sql")

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    async def _conn(self):
        if DatabaseConnection.get_pool() is None:
            raise RuntimeError(
                "DatabaseConnection pool not initialized — SqlMemoryStore "
                "requires PostgreSQL. Falling back to InMemoryStore."
            )
        return DatabaseConnection

    def _scope_where(self, scope: MemoryScope, tenant_col: str = "tenant_id",
                     user_col: str = "user_id", sess_col: str = "session_id",
                     app_col: str = "application_id") -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if scope.tenant_id != "*":
            clauses.append(f"{tenant_col} = ${len(params) + 1}")
            params.append(scope.tenant_id)
        if scope.user_id:
            clauses.append(f"{user_col} = ${len(params) + 1}")
            params.append(scope.user_id)
        else:
            clauses.append(f"({user_col} IS NULL OR {user_col} = '')")
        if scope.session_id:
            clauses.append(f"{sess_col} = ${len(params) + 1}")
            params.append(scope.session_id)
        if scope.application_id:
            clauses.append(f"{app_col} = ${len(params) + 1}")
            params.append(scope.application_id)
        where = " AND ".join(clauses) if clauses else "TRUE"
        return where, params

    def _compute_score(self, item: MemoryItem, query: MemoryQuery) -> float:
        score = 0.5
        if query.query:
            q = query.query.lower()
            content_lower = item.content.lower()
            if q in content_lower:
                score += 0.3 * (len(q) / max(len(content_lower), 1))
            if any(t.lower() in q for t in item.tags):
                score += 0.2
        if query.tags:
            matching_tags = sum(1 for t in query.tags if t in item.tags)
            if matching_tags > 0:
                score += 0.2 * (matching_tags / max(len(query.tags), 1))
        score += item.importance * 0.1
        return min(score, 1.0)

    # ------------------------------------------------------------------
    # MemoryStore protocol
    # ------------------------------------------------------------------

    async def create(self, item: MemoryItem) -> MemoryItem:
        db = await self._conn()
        fq_id = ScopedMemoryId(memory_id=item.memory_id, scope=item.scope).fully_qualified()
        existing = await db.fetchval(
            "SELECT 1 FROM memory_items WHERE memory_id = $1 AND tenant_id = $2",
            item.memory_id, item.scope.tenant_id,
        )
        if existing:
            raise MemoryValidationError(
                f"Memory item {fq_id} already exists",
                context={"memory_id": item.memory_id, "scope": item.scope.scope_key()},
            )
        await db.execute(
            """
            INSERT INTO memory_items (
                memory_id, tenant_id, user_id, session_id, application_id,
                memory_type, domain, content, content_summary, importance,
                confidence, sensitivity, source, provenance, retention_policy,
                status, parent_id, related_ids, tags, metadata, embedding,
                version, access_count, created_at, updated_at, accessed_at,
                expires_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                $21, $22, $23, $24, $25, $26, $27
            )
            """,
            item.memory_id,
            item.scope.tenant_id,
            item.scope.user_id,
            item.scope.session_id,
            item.scope.application_id,
            item.memory_type.value,
            item.domain.value,
            item.content,
            item.content_summary,
            item.importance,
            item.confidence,
            item.sensitivity.value,
            item.source,
            item.provenance,
            item.retention_policy,
            item.status.value,
            item.parent_id,
            json.dumps(item.related_ids) if item.related_ids else "[]",
            json.dumps(item.tags) if item.tags else "[]",
            json.dumps(item.metadata) if item.metadata else "{}",
            json.dumps(list(item.embedding)) if item.embedding else None,
            item.version,
            item.access_count,
            item.created_at,
            item.updated_at,
            item.accessed_at,
            item.expires_at,
        )
        self._log.debug("store.created", fq_id=fq_id, memory_type=item.memory_type.value)
        return item

    async def read(self, scoped_id: ScopedMemoryId) -> MemoryItem | None:
        db = await self._conn()
        row = await db.fetchrow(
            """
            SELECT * FROM memory_items
            WHERE memory_id = $1 AND tenant_id = $2
              AND (user_id = $3 OR ($3 IS NULL AND user_id IS NULL))
              AND (session_id = $4 OR ($4 IS NULL AND session_id IS NULL))
              AND (application_id = $5 OR ($5 IS NULL AND application_id IS NULL))
            """,
            scoped_id.memory_id,
            scoped_id.scope.tenant_id,
            scoped_id.scope.user_id,
            scoped_id.scope.session_id,
            scoped_id.scope.application_id,
        )
        if row is None:
            return None
        return _deserialize_item(row)

    async def update(self, item: MemoryItem) -> MemoryItem:
        db = await self._conn()
        existing = await self.read(
            ScopedMemoryId(memory_id=item.memory_id, scope=item.scope)
        )
        if existing is None:
            raise MemoryNotFoundError(
                f"Memory item {item.memory_id} not found",
                context={"memory_id": item.memory_id},
            )
        await db.execute(
            """
            UPDATE memory_items SET
                content = $1, content_summary = $2, importance = $3,
                confidence = $4, sensitivity = $5, source = $6,
                provenance = $7, retention_policy = $8, status = $9,
                parent_id = $10, related_ids = $11, tags = $12,
                metadata = $13, embedding = $14, version = $15,
                access_count = $16, updated_at = $17, accessed_at = $18,
                expires_at = $19
            WHERE memory_id = $20 AND tenant_id = $21
              AND (user_id = $22 OR ($22 IS NULL AND user_id IS NULL))
              AND (session_id = $23 OR ($23 IS NULL AND session_id IS NULL))
              AND (application_id = $24 OR ($24 IS NULL AND application_id IS NULL))
            """,
            item.content, item.content_summary, item.importance,
            item.confidence, item.sensitivity.value, item.source,
            item.provenance, item.retention_policy, item.status.value,
            item.parent_id,
            json.dumps(item.related_ids) if item.related_ids else "[]",
            json.dumps(item.tags) if item.tags else "[]",
            json.dumps(item.metadata) if item.metadata else "{}",
            json.dumps(list(item.embedding)) if item.embedding else None,
            item.version, item.access_count, item.updated_at,
            item.accessed_at, item.expires_at,
            item.memory_id, item.scope.tenant_id,
            item.scope.user_id, item.scope.session_id, item.scope.application_id,
        )
        self._log.debug("store.updated", fq_id=item.memory_id, version=item.version)
        return item

    async def delete(self, scoped_id: ScopedMemoryId) -> bool:
        db = await self._conn()
        result = await db.execute(
            """
            DELETE FROM memory_items
            WHERE memory_id = $1 AND tenant_id = $2
              AND (user_id = $3 OR ($3 IS NULL AND user_id IS NULL))
              AND (session_id = $4 OR ($4 IS NULL AND session_id IS NULL))
              AND (application_id = $5 OR ($5 IS NULL AND application_id IS NULL))
            """,
            scoped_id.memory_id,
            scoped_id.scope.tenant_id,
            scoped_id.scope.user_id,
            scoped_id.scope.session_id,
            scoped_id.scope.application_id,
        )
        self._log.debug("store.deleted", fq_id=scoped_id.fully_qualified())
        return result != "DELETE 0"

    async def archive(self, scoped_id: ScopedMemoryId) -> bool:
        db = await self._conn()
        result = await db.execute(
            """
            UPDATE memory_items SET
                status = 'archived',
                updated_at = NOW()
            WHERE memory_id = $1 AND tenant_id = $2
              AND (user_id = $3 OR ($3 IS NULL AND user_id IS NULL))
              AND (session_id = $4 OR ($4 IS NULL AND session_id IS NULL))
              AND (application_id = $5 OR ($5 IS NULL AND application_id IS NULL))
              AND status = 'active'
            """,
            scoped_id.memory_id, scoped_id.scope.tenant_id,
            scoped_id.scope.user_id, scoped_id.scope.session_id,
            scoped_id.scope.application_id,
        )
        return result != "UPDATE 0"

    async def restore(self, scoped_id: ScopedMemoryId) -> bool:
        db = await self._conn()
        result = await db.execute(
            """
            UPDATE memory_items SET
                status = 'active',
                updated_at = NOW()
            WHERE memory_id = $1 AND tenant_id = $2
              AND (user_id = $3 OR ($3 IS NULL AND user_id IS NULL))
              AND (session_id = $4 OR ($4 IS NULL AND session_id IS NULL))
              AND (application_id = $5 OR ($5 IS NULL AND application_id IS NULL))
              AND status IN ('archived', 'expired')
            """,
            scoped_id.memory_id, scoped_id.scope.tenant_id,
            scoped_id.scope.user_id, scoped_id.scope.session_id,
            scoped_id.scope.application_id,
        )
        return result != "UPDATE 0"

    async def archive_many(self, fq_ids: list[str]) -> int:
        if not fq_ids:
            return 0
        db = await self._conn()
        conditions: list[str] = []
        params: list[Any] = []
        for fq_id in fq_ids:
            tenant, user, sess, app, mem_id = _parse_fq_id(fq_id)
            idx = len(params) + 1
            cond_parts = [f"(memory_id = ${idx} AND tenant_id = ${idx + 1}"]
            params.extend([mem_id, tenant])
            idx += 2
            if user is not None:
                cond_parts.append(f"AND user_id = ${idx}")
                params.append(user)
                idx += 1
            if sess is not None:
                cond_parts.append(f"AND session_id = ${idx}")
                params.append(sess)
                idx += 1
            if app is not None:
                cond_parts.append(f"AND application_id = ${idx}")
                params.append(app)
                idx += 1
            cond_parts.append(")")
            conditions.append(" ".join(cond_parts))
        where = " OR ".join(conditions)
        result = await db.execute(
            f"UPDATE memory_items SET status = 'archived', updated_at = NOW() "
            f"WHERE status = 'active' AND ({where})",
            *params,
        )
        self._log.debug("store.archive_many", count=result)
        return int(result.split()[-1]) if result and result != "UPDATE 0" else 0

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        db = await self._conn()
        clauses: list[str] = []
        params: list[Any] = []

        if query.scopes:
            scope_conditions: list[str] = []
            for scope in query.scopes:
                where, p = self._scope_where(scope)
                scope_conditions.append(f"({where})")
                params.extend(p)
            if len(query.scopes) == 1:
                clauses.append(scope_conditions[0])
            else:
                clauses.append(f"({' OR '.join(scope_conditions)})")
        else:
            clauses.append(self._scope_where(MemoryScope(tenant_id="*"))[0])

        if query.memory_types:
            type_vals = [t.value for t in query.memory_types]
            placeholders = ", ".join(f"${len(params) + i + 1}" for i in range(len(type_vals)))
            clauses.append(f"memory_type IN ({placeholders})")
            params.extend(type_vals)

        if query.status is not None:
            clauses.append(f"status = ${len(params) + 1}")
            params.append(query.status.value)
        else:
            clauses.append("status = 'active'")

        if query.tags:
            tag_arr = list(query.tags)
            placeholders = ", ".join(f"${len(params) + i + 1}" for i in range(len(tag_arr)))
            clauses.append(f"tags ?| array[{placeholders}]::text[]")
            params.extend(tag_arr)

        clauses.append(f"importance >= ${len(params) + 1} AND importance <= ${len(params) + 2}")
        params.extend([query.importance_min, query.importance_max])

        if query.query:
            clauses.append(
                f"(content ILIKE ${len(params) + 1} OR tags::text ILIKE ${len(params) + 2})"
            )
            params.extend([f"%{query.query}%", f"%{query.query}%"])

        where = " AND ".join(clauses)
        rows = await db.fetch(
            f"SELECT * FROM memory_items WHERE {where} "
            f"ORDER BY importance DESC, created_at DESC "
            f"LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}",
            *params, query.limit, query.offset,
        )
        results: list[MemorySearchResult] = []
        for row in rows:
            item = _deserialize_item(row)
            score = self._compute_score(item, query)
            if score >= query.score_threshold:
                results.append(MemorySearchResult(memory=item, score=score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[query.offset: query.offset + query.limit]

    async def list_by_scope(
        self,
        scope: MemoryScope,
        memory_type: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[MemoryItem]:
        db = await self._conn()
        where, params = self._scope_where(scope)
        if memory_type:
            params.append(memory_type)
            where += f" AND memory_type = ${len(params)}"
        if status:
            params.append(status)
            where += f" AND status = ${len(params)}"
        rows = await db.fetch(
            f"SELECT * FROM memory_items WHERE {where} "
            f"ORDER BY created_at DESC OFFSET ${len(params) + 1} LIMIT ${len(params) + 2}",
            *params, offset, limit,
        )
        return [_deserialize_item(row) for row in rows]

    async def count_by_scope(
        self,
        scope: MemoryScope,
        memory_type: str | None = None,
        status: str | None = None,
    ) -> int:
        db = await self._conn()
        where, params = self._scope_where(scope)
        if memory_type:
            params.append(memory_type)
            where += f" AND memory_type = ${len(params)}"
        if status:
            params.append(status)
            where += f" AND status = ${len(params)}"
        result = await db.fetchval(
            f"SELECT COUNT(*) FROM memory_items WHERE {where}", *params
        )
        return result or 0

    async def expire_before(self, before: float, batch_size: int = 100) -> list[str]:
        db = await self._conn()
        rows = await db.fetch(
            """
            SELECT tenant_id, user_id, session_id, application_id, memory_id
            FROM memory_items
            WHERE status = 'active' AND expires_at IS NOT NULL AND expires_at <= to_timestamp($1)
            ORDER BY expires_at ASC
            LIMIT $2
            """,
            before, batch_size,
        )
        fq_ids: list[str] = []
        for row in rows:
            fq_ids.append(
                _fq_id(
                    row["tenant_id"], row["user_id"], row["session_id"],
                    row["application_id"], row["memory_id"],
                )
            )
        return fq_ids

    async def delete_many(self, fq_ids: list[str]) -> int:
        if not fq_ids:
            return 0
        db = await self._conn()
        conditions: list[str] = []
        params: list[Any] = []
        for fq_id in fq_ids:
            tenant, user, sess, app, mem_id = _parse_fq_id(fq_id)
            idx = len(params) + 1
            cond_parts = [f"(memory_id = ${idx} AND tenant_id = ${idx + 1}"]
            params.extend([mem_id, tenant])
            idx += 2
            if user is not None:
                cond_parts.append(f"AND user_id = ${idx}")
                params.append(user)
                idx += 1
            if sess is not None:
                cond_parts.append(f"AND session_id = ${idx}")
                params.append(sess)
                idx += 1
            if app is not None:
                cond_parts.append(f"AND application_id = ${idx}")
                params.append(app)
                idx += 1
            cond_parts.append(")")
            conditions.append(" ".join(cond_parts))
        where = " OR ".join(conditions)
        result = await db.execute(
            f"DELETE FROM memory_items WHERE ({where})", *params
        )
        count = int(result.split()[-1]) if result and result != "DELETE 0" else 0
        self._log.debug("store.delete_many", count=count)
        return count

    async def clear_scope(self, scope: MemoryScope) -> int:
        db = await self._conn()
        where, params = self._scope_where(scope)
        result = await db.execute(
            f"DELETE FROM memory_items WHERE {where}", *params,
        )
        count = int(result.split()[-1]) if result and result != "DELETE 0" else 0
        self._log.debug("store.clear_scope", scope=scope.scope_key(), count=count)
        return count


__all__ = ["SqlMemoryStore"]
