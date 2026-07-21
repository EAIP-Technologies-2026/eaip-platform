"""IndexManager — create, update, delete, build, search indices."""

from __future__ import annotations

from typing import Any

from eaip.searchidx.exceptions import IndexBuildError, IndexNotFoundError
from eaip.searchidx.models import IndexJob, SearchIndex
from eaip.shared.time import utc_now


class IndexManager:
    """Manages search indices with build pipeline."""

    def __init__(self) -> None:
        """Initialize the index manager."""
        self._indices: dict[str, SearchIndex] = {}
        self._jobs: dict[str, IndexJob] = {}
        self._job_counter: int = 0

    def create(self, index: SearchIndex) -> SearchIndex:
        """Create a new search index."""
        self._indices[index.id] = index
        return index

    def get(self, index_id: str) -> SearchIndex | None:
        """Get an index by id, or None."""
        return self._indices.get(index_id)

    def get_index(self, index_id: str) -> SearchIndex:
        """Get an index by id, raising if not found."""
        idx = self.get(index_id)
        if idx is None:
            raise IndexNotFoundError(
                f"Index {index_id!r} not found.",
                context={"index_id": index_id},
            )
        return idx

    def update(self, index_id: str, **kwargs: Any) -> SearchIndex:
        """Update fields on an index."""
        existing = self.get_index(index_id)
        updated = existing.model_copy(update=kwargs)
        self._indices[index_id] = updated
        return updated

    def delete(self, index_id: str) -> SearchIndex:
        """Delete an index and its jobs."""
        idx = self._indices.pop(index_id, None)
        if idx is None:
            raise IndexNotFoundError(
                f"Index {index_id!r} not found.",
                context={"index_id": index_id},
            )
        self._jobs = {jid: j for jid, j in self._jobs.items() if j.index_id != index_id}
        return idx

    def list_indices(self) -> list[SearchIndex]:
        """Return all indices."""
        return list(self._indices.values())

    async def build_index(self, index_id: str) -> IndexJob:
        """Start a full build job for an index."""
        index = self.get_index(index_id)
        self._job_counter += 1
        job = IndexJob(
            id=f"job-{self._job_counter}",
            index_id=index_id,
            type="full",
            status="running",
            started_at=utc_now(),
        )
        self._jobs[job.id] = job
        completed = job.model_copy(
            update={
                "status": "completed",
                "documents_processed": 100,
                "completed_at": utc_now(),
            }
        )
        self._jobs[job.id] = completed
        self._indices[index_id] = index.model_copy(
            update={
                "status": "ready",
                "document_count": 100,
                "last_built_at": utc_now(),
            }
        )
        return completed

    async def incremental_index(self, index_id: str) -> IndexJob:
        """Start an incremental indexing job."""
        index = self.get_index(index_id)
        if index.status != "ready":
            raise IndexBuildError(
                f"Cannot incrementally index index in status {index.status!r}.",
                context={"index_id": index_id, "status": index.status},
            )
        self._job_counter += 1
        job = IndexJob(
            id=f"job-{self._job_counter}",
            index_id=index_id,
            type="incremental",
            status="running",
            started_at=utc_now(),
        )
        self._jobs[job.id] = job
        completed = job.model_copy(
            update={
                "status": "completed",
                "documents_processed": 10,
                "completed_at": utc_now(),
            }
        )
        self._jobs[job.id] = completed
        self._indices[index_id] = index.model_copy(
            update={
                "document_count": index.document_count + 10,
                "last_built_at": utc_now(),
            }
        )
        return completed

    async def get_index_status(self, index_id: str) -> dict[str, Any]:
        """Return status info for an index."""
        index = self.get_index(index_id)
        index_jobs = [j for j in self._jobs.values() if j.index_id == index_id]
        return {
            "id": index.id,
            "name": index.name,
            "status": index.status,
            "document_count": index.document_count,
            "last_built_at": index.last_built_at,
            "total_jobs": len(index_jobs),
            "recent_jobs": [j.id for j in index_jobs[-5:]],
        }

    async def search_index(self, index_id: str, query: str) -> list[dict[str, Any]]:
        """Search an index (simulated)."""
        index = self.get_index(index_id)
        if index.status != "ready":
            raise IndexBuildError(
                f"Cannot search index in status {index.status!r}.",
                context={"index_id": index_id, "status": index.status},
            )
        return [{"id": index.id, "name": index.name, "query": query, "score": 1.0}]

    async def suggest(self, index_id: str, prefix: str) -> list[str]:
        """Return search suggestions for a prefix."""
        index = self.get_index(index_id)
        if index.status != "ready":
            raise IndexBuildError(
                f"Cannot suggest on index in status {index.status!r}.",
                context={"index_id": index_id, "status": index.status},
            )
        field_names = [f.name for f in index.fields if f.searchable]
        return [f for f in field_names if f.startswith(prefix.lower())]


__all__ = ["IndexManager"]
