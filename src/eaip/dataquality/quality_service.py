"""DataQualityService — run checks, profile data, detect anomalies."""

from __future__ import annotations

import statistics
import time
from typing import Any, Literal, cast

from eaip.dataquality.models import DataQualityConfig, QualityResult, QualityRule
from eaip.dataquality.rule_engine import QualityRuleEngine
from eaip.shared.time import utc_now


class DataQualityService:
    """High-level service for data quality operations, profiling, and anomaly detection."""

    def __init__(
        self,
        rule_engine: QualityRuleEngine,
        config: DataQualityConfig | None = None,
    ) -> None:
        """Initialize the data quality service."""
        self._rule_engine = rule_engine
        self._config = config or DataQualityConfig()

    @property
    def rule_engine(self) -> QualityRuleEngine:
        """Return the rule engine."""
        return self._rule_engine

    async def run_quality_check(
        self,
        data: list[dict[str, Any]],
        rules: list[QualityRule],
    ) -> QualityResult:
        """Run a quality check on a dataset using specified rules."""
        started_at = utc_now()
        t0 = time.monotonic()
        total = len(rules)
        passed = 0
        failed = 0
        errors: list[str] = []

        for record in data:
            for rule in rules:
                if not rule.enabled:
                    continue
                try:
                    rule_passed, _violations = await self._rule_engine.validate(rule, record)
                    if rule_passed:
                        passed += 1
                    else:
                        failed += 1
                except Exception as exc:
                    errors.append(str(exc))
                    failed += 1

        duration_ms = (time.monotonic() - t0) * 1000
        status: str = "passed" if failed == 0 else "failed"
        if errors:
            status = "error"

        return QualityResult(
            id=f"dq-{id(data)}-{id(rules)}",
            check_id="ad-hoc",
            status=cast("Literal['passed', 'failed', 'error']", status),
            total_checks=total * len(data),
            passed_checks=passed,
            failed_checks=failed,
            errors=tuple(errors),
            started_at=started_at,
            completed_at=utc_now(),
            duration_ms=round(duration_ms, 2),
        )

    async def profile_data(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Profile a dataset and return summary statistics."""
        if not data:
            return {"record_count": 0, "fields": {}}

        fields: dict[str, Any] = {}
        for record in data:
            for key, value in record.items():
                if key not in fields:
                    fields[key] = {"type": type(value).__name__, "values": []}
                fields[key]["values"].append(value)

        profile: dict[str, Any] = {"record_count": len(data), "fields": {}}
        for field_name, info in fields.items():
            vals = info["values"]
            profile["fields"][field_name] = {
                "type": info["type"],
                "count": len(vals),
                "unique_count": len({str(v) for v in vals}),
                "null_count": sum(1 for v in vals if v is None),
                "non_null_count": sum(1 for v in vals if v is not None),
            }
            numeric_vals = [v for v in vals if isinstance(v, (int, float))]
            if numeric_vals:
                profile["fields"][field_name].update(
                    {
                        "min": min(numeric_vals),
                        "max": max(numeric_vals),
                        "mean": round(statistics.mean(numeric_vals), 4),
                        "median": round(statistics.median(numeric_vals), 4),
                        "stdev": round(statistics.stdev(numeric_vals), 4)
                        if len(numeric_vals) > 1
                        else 0.0,
                    }
                )
        return profile

    async def detect_anomalies(
        self,
        data: list[dict[str, Any]],
        field: str,
    ) -> list[dict[str, Any]]:
        """Detect anomalies in a specific field using z-score."""
        values = []
        for record in data:
            v = record.get(field)
            if isinstance(v, (int, float)):
                values.append(v)

        if len(values) < 3:  # noqa: PLR2004
            return []

        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        if stdev == 0:
            return []

        anomalies: list[dict[str, Any]] = []
        for i, record in enumerate(data):
            v = record.get(field)
            if isinstance(v, (int, float)):
                z_score = (v - mean) / stdev
                if abs(z_score) > 2.0:  # noqa: PLR2004
                    anomalies.append(
                        {
                            "index": i,
                            "field": field,
                            "value": v,
                            "z_score": round(z_score, 4),
                            "severity": "error" if abs(z_score) > 3.0 else "warning",  # noqa: PLR2004
                        }
                    )
        return anomalies

    async def get_data_profile(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a comprehensive data profile (alias for profile_data)."""
        return await self.profile_data(data)


__all__ = ["DataQualityService"]
