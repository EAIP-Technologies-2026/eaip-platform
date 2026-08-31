"""MethodologyRegistry — tenant-isolated methodology lifecycle.

Storage key is ``tenant_id:methodology_id:version`` so multiple versions can
coexist. The registry enforces: new version creates a new record and marks the
previous active version as deprecated.
"""

from __future__ import annotations

from typing import Any

from eaip.logging.context import get_logger
from eaip.methodology.models import MethodologyCategory, MethodologyRecord
from eaip.shared.time import utc_now

log = get_logger("eaip.methodology.registry")


def _physical_key(tenant_id: str, methodology_id: str, version: str) -> str:
    return f"{tenant_id}:{methodology_id}:{version}"


def _logical_prefix(tenant_id: str, methodology_id: str) -> str:
    return f"{tenant_id}:{methodology_id}:"


class MethodologyRegistry:
    """Tenant-isolated registry for methodology records with versioning."""

    def __init__(self) -> None:
        # physical key -> record (supports multiple versions)
        self._store: dict[str, MethodologyRecord] = {}

    # -- helpers --

    def _latest_active(self, tenant_id: str, methodology_id: str) -> MethodologyRecord | None:
        prefix = _logical_prefix(tenant_id, methodology_id)
        candidates = [v for k, v in self._store.items() if k.startswith(prefix) and v.lifecycle_status == "active"]
        if not candidates:
            return None
        # naive semver sort: split by dot
        def _ver_key(r: MethodologyRecord) -> tuple[int, ...]:
            try:
                return tuple(int(p) for p in r.version.split("."))
            except Exception:
                return (0,)

        candidates.sort(key=_ver_key, reverse=True)
        return candidates[0]

    def _all_versions(self, tenant_id: str, methodology_id: str) -> list[MethodologyRecord]:
        prefix = _logical_prefix(tenant_id, methodology_id)
        return [v for k, v in self._store.items() if k.startswith(prefix)]

    # -- CRUD --

    def register(self, record: MethodologyRecord) -> MethodologyRecord:
        """Register a methodology record with versioning.

        If a record with the same ``methodology_id``/``version`` already exists,
        it is replaced. If a new version is introduced and an older version is
        active, the older active version is marked deprecated.

        Returns:
            The stored record (with updated timestamps).
        """
        key = _physical_key(record.tenant_id, record.methodology_id, record.version)
        now = utc_now()

        # detect if this is a new version vs same version overwrite
        existing_versions = self._all_versions(record.tenant_id, record.methodology_id)
        is_new_version = all(r.version != record.version for r in existing_versions) and bool(existing_versions)

        if is_new_version:
            # deprecate previous active version(s)
            for r in existing_versions:
                if r.lifecycle_status == "active":
                    pkey = _physical_key(r.tenant_id, r.methodology_id, r.version)
                    deprecated = r.model_copy(update={"lifecycle_status": "deprecated", "updated_at": now})
                    self._store[pkey] = deprecated
                    log.info(
                        "methodology.deprecated",
                        methodology_id=r.methodology_id,
                        version=r.version,
                        tenant_id=r.tenant_id,
                        superseded_by=record.version,
                    )

        stored = record.model_copy(update={"created_at": record.created_at, "updated_at": now})
        # if overwriting same version, preserve original created_at
        if key in self._store:
            stored = stored.model_copy(update={"created_at": self._store[key].created_at})
        self._store[key] = stored
        log.info(
            "methodology.registered",
            methodology_id=record.methodology_id,
            version=record.version,
            tenant_id=record.tenant_id,
            category=str(record.category),
        )
        return stored

    def get(self, methodology_id: str, tenant_id: str, version: str | None = None) -> MethodologyRecord | None:
        """Get a methodology by id.

        If version is None, returns the latest active, else falls back to any
        version.
        """
        if version is not None:
            return self._store.get(_physical_key(tenant_id, methodology_id, version))
        latest = self._latest_active(tenant_id, methodology_id)
        if latest is not None:
            return latest
        # fallback: any version
        versions = self._all_versions(tenant_id, methodology_id)
        if not versions:
            return None

        def _ver_key(r: MethodologyRecord) -> tuple[int, ...]:
            try:
                return tuple(int(p) for p in r.version.split("."))
            except Exception:
                return (0,)

        versions.sort(key=_ver_key, reverse=True)
        return versions[0]

    def list_for_tenant(self, tenant_id: str, include_deprecated: bool = False) -> list[MethodologyRecord]:
        """List all methodologies for a tenant."""
        prefix = f"{tenant_id}:"
        results = [v for k, v in self._store.items() if k.startswith(prefix)]
        if not include_deprecated:
            results = [r for r in results if r.lifecycle_status == "active"]
        return results

    def list_versions(self, methodology_id: str, tenant_id: str) -> list[MethodologyRecord]:
        """List all versions for a given methodology."""
        versions = self._all_versions(tenant_id, methodology_id)

        def _ver_key(r: MethodologyRecord) -> tuple[int, ...]:
            try:
                return tuple(int(p) for p in r.version.split("."))
            except Exception:
                return (0,)

        versions.sort(key=_ver_key, reverse=True)
        return versions

    def search(
        self,
        tenant_id: str,
        query: str = "",
        category: str = "",
        domain: str = "",
        include_deprecated: bool = False,
    ) -> list[MethodologyRecord]:
        """Search methodologies for a tenant.

        Filters by free-text query (name/provider/capabilities), category and
        domain.
        """
        results = self.list_for_tenant(tenant_id, include_deprecated=include_deprecated)
        if query:
            q = query.lower()
            results = [
                r
                for r in results
                if q in r.name.lower() or q in r.provider.lower() or any(q in c.lower() for c in r.capabilities)
            ]
        if category:
            # allow enum value or raw string
            cat_val = category.lower()
            results = [r for r in results if r.category.value.lower() == cat_val or str(r.category).lower() == cat_val]
        if domain:
            d = domain.lower()
            results = [r for r in results if any(d == sd.lower() for sd in r.supported_domains)]
        return results

    def recommend(
        self,
        tenant_id: str,
        task: str = "",
        domain: str = "",
        latency_budget: float | None = None,
        cost_budget: float | None = None,
        category: str = "",
        limit: int = 10,
    ) -> list[MethodologyRecord]:
        """Recommend methodologies sorted by benchmark_score descending.

        Applies optional budgets (latency/cost) and domain/task relevance.
        Only active methodologies are considered.
        """
        results = self.list_for_tenant(tenant_id, include_deprecated=False)
        if category:
            cat_val = category.lower()
            results = [r for r in results if r.category.value.lower() == cat_val]
        if domain:
            d = domain.lower()
            results = [r for r in results if any(d == sd.lower() for sd in r.supported_domains)]
        if task:
            t = task.lower()
            # prefer methodologies whose capabilities or name mention task keywords
            def _relevance(r: MethodologyRecord) -> int:
                score = 0
                if t in r.name.lower():
                    score += 2
                for cap in r.capabilities:
                    if t in cap.lower():
                        score += 1
                for req_val in r.input_requirements.values():
                    if isinstance(req_val, str) and t in req_val.lower():
                        score += 1
                return score

            # keep all but boost relevance — do not filter, sort later by relevance + benchmark
            results.sort(key=lambda r: (_relevance(r), r.benchmark_score), reverse=True)
        if latency_budget is not None:
            try:
                b = float(latency_budget)
                results = [r for r in results if float(r.latency) <= b]
            except Exception:
                pass
        if cost_budget is not None:
            try:
                b = float(cost_budget)
                results = [r for r in results if float(r.cost) <= b]
            except Exception:
                pass
        # final sort by benchmark descending; if task was provided the sort above already
        # incorporated benchmark as secondary — re-sort if no task filter was applied
        if not task:
            results.sort(key=lambda r: r.benchmark_score, reverse=True)
        return results[: max(1, min(limit, 100))]

    def evaluate(
        self,
        methodology_id: str,
        tenant_id: str,
        metrics: dict[str, Any],
        version: str | None = None,
    ) -> MethodologyRecord | None:
        """Update reliability/latency (and optionally other) metrics for a methodology.

        Expected metrics keys: ``reliability``, ``latency``, ``benchmark_score``,
        ``cost`` (all optional). Returns updated record or None if not found.
        """
        rec = self.get(methodology_id, tenant_id, version=version)
        if rec is None:
            return None
        updates: dict[str, Any] = {"updated_at": utc_now()}
        if "reliability" in metrics:
            try:
                rel = float(metrics["reliability"])
                rel = max(0.0, min(1.0, rel))
                updates["reliability"] = rel
            except Exception:
                pass
        if "latency" in metrics:
            try:
                lat = float(metrics["latency"])
                updates["latency"] = max(0.0, lat)
            except Exception:
                pass
        if "benchmark_score" in metrics:
            try:
                updates["benchmark_score"] = float(metrics["benchmark_score"])
            except Exception:
                pass
        if "cost" in metrics:
            try:
                updates["cost"] = max(0.0, float(metrics["cost"]))
            except Exception:
                pass
        # allow any other direct field updates if key matches model
        # (defensive: only known numeric fields)
        new = rec.model_copy(update=updates)
        key = _physical_key(new.tenant_id, new.methodology_id, new.version)
        self._store[key] = new
        log.info(
            "methodology.evaluated",
            methodology_id=methodology_id,
            version=new.version,
            tenant_id=tenant_id,
            metrics=list(metrics.keys()),
        )
        return new


__all__ = ["MethodologyRegistry"]
