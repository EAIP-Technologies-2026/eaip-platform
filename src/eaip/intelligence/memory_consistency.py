from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any

from eaip.intelligence.models import MemoryConsistencyReport
from eaip.shared.time import utc_now


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:12]


class MemoryConsistencyEngine:
    def __init__(self) -> None:
        self._reports: dict[str, MemoryConsistencyReport] = {}

    def analyze(self, tenant_id: str, memories: list[dict[str, Any]], knowledge_items: list[dict[str, Any]] | None = None) -> MemoryConsistencyReport:
        knowledge_items = knowledge_items or []
        contradictions: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []
        stale: list[dict[str, Any]] = []

        seen_hash: dict[str, dict[str, Any]] = {}
        for m in memories:
            h = _hash_content(str(m.get("content", "")))
            if h in seen_hash:
                duplicates.append({"original": seen_hash[h].get("memory_id", seen_hash[h].get("id")), "duplicate": m.get("memory_id", m.get("id")), "hash": h})
            else:
                seen_hash[h] = m

        content_map: dict[str, list[dict[str, Any]]] = {}
        for m in memories:
            key = str(m.get("content", ""))[:40]
            content_map.setdefault(key, []).append(m)
        for k, vals in knowledge_items and {} or {}.items():
            pass
        for item in knowledge_items:
            for mem in memories:
                mc = str(mem.get("content", "")).lower()
                kc = str(item.get("content", item.get("title", ""))).lower()
                if mc and kc and mc[:30] == kc[:30] and mc != kc:
                    contradictions.append({"memory": mem.get("memory_id", mem.get("id")), "knowledge": item.get("document_id", item.get("id")), "reason": "content mismatch on same prefix"})

        now = utc_now()
        for m in memories:
            freshness = m.get("freshness")
            created = m.get("created_at") or m.get("createdAt")
            try:
                if isinstance(created, str):
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                elif isinstance(created, datetime):
                    dt = created
                else:
                    continue
                if now - dt > timedelta(days=90):
                    stale.append({"id": m.get("memory_id", m.get("id")), "age_days": (now - dt).days, "reason": "older than 90 days"})
            except Exception:
                continue
            if m.get("confidence", 1) < 0.3:
                stale.append({"id": m.get("memory_id", m.get("id")), "reason": "low confidence <0.3"})

        report = MemoryConsistencyReport(report_id=f"mem-cons-{uuid.uuid4().hex[:8]}", tenant_id=tenant_id, contradictions=tuple(contradictions), duplicates=tuple(duplicates), stale_items=tuple(stale))
        self._reports[report.report_id] = report
        return report

    def reconcile(self, tenant_id: str, report_id: str, resolution: str = "human_review") -> dict[str, Any]:
        report = self._reports.get(report_id)
        if not report or report.tenant_id != tenant_id:
            raise ValueError("report not found")
        return {"report_id": report_id, "tenant_id": tenant_id, "resolution": resolution, "status": "proposed" if resolution == "human_review" else "resolved"}
