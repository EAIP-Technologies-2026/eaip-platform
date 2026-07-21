"""DriftDetector — capture snapshots, detect and resolve configuration drift."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from eaip.configdrift.events import (
    DriftDetected,
    DriftResolved,
    SnapshotCaptured,
)
from eaip.configdrift.exceptions import (
    DriftDetectionError,
    SnapshotNotFoundError,
)
from eaip.configdrift.models import (
    ConfigSnapshot,
    DriftConfig,
    DriftReport,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class DriftDetector:
    def __init__(self, config: DriftConfig | None = None) -> None:
        self._config = config or DriftConfig()
        self._snapshots: dict[str, ConfigSnapshot] = {}
        self._reports: dict[str, DriftReport] = {}
        self._baselines: dict[str, str] = {}
        self._report_counter: int = 0
        self._log = get_logger("eaip.configdrift.detector")

    @property
    def config(self) -> DriftConfig:
        return self._config

    @staticmethod
    def _compute_checksum(config_data: dict[str, Any]) -> str:
        raw = json.dumps(config_data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def capture_snapshot(
        self,
        resource_id: str,
        config_data: dict[str, Any],
        snapshot_id: str | None = None,
    ) -> ConfigSnapshot:
        sid = snapshot_id or f"snap_{resource_id}_{int(utc_now().timestamp())}"
        checksum = self._compute_checksum(config_data)
        snapshot = ConfigSnapshot(
            id=sid,
            resource_id=resource_id,
            config_data=config_data,
            checksum=checksum,
        )
        self._snapshots[sid] = snapshot
        SnapshotCaptured(snapshot_id=sid, resource_id=resource_id)
        self._log.info("configdrift.snapshot.captured", id=sid, resource=resource_id)
        return snapshot

    async def get_snapshot(self, snapshot_id: str) -> ConfigSnapshot:
        snap = self._snapshots.get(snapshot_id)
        if snap is None:
            raise SnapshotNotFoundError(f"Snapshot '{snapshot_id}' not found")
        return snap

    async def list_snapshots(self, resource_id: str | None = None) -> list[ConfigSnapshot]:
        if resource_id is not None:
            return [s for s in self._snapshots.values() if s.resource_id == resource_id]
        return list(self._snapshots.values())

    async def compare_snapshots(
        self,
        baseline_id: str,
        current_id: str,
    ) -> list[dict[str, Any]]:
        baseline = await self.get_snapshot(baseline_id)
        current = await self.get_snapshot(current_id)

        differences: list[dict[str, Any]] = []
        all_keys = set(baseline.config_data.keys()) | set(current.config_data.keys())
        for key in all_keys:
            old_val = baseline.config_data.get(key)
            new_val = current.config_data.get(key)
            if old_val != new_val:
                differences.append(
                    {
                        "path": key,
                        "baseline_value": old_val,
                        "current_value": new_val,
                        "changed": old_val is not None and new_val is not None,
                        "added": old_val is None,
                        "removed": new_val is None,
                    }
                )
        return differences

    async def detect_drift(
        self,
        resource_id: str,
        current_id: str,
    ) -> DriftReport:
        baseline_id = self._baselines.get(resource_id)
        if baseline_id is None:
            raise DriftDetectionError(
                f"No baseline set for resource '{resource_id}'. Call set_baseline first."
            )
        differences = await self.compare_snapshots(baseline_id, current_id)
        self._report_counter += 1
        severity = self._config.default_severity
        report = DriftReport(
            id=f"dr_{self._report_counter}",
            resource_id=resource_id,
            baseline_id=baseline_id,
            current_id=current_id,
            differences=differences[: self._config.max_differences_per_report],
            severity=severity,
        )
        self._reports[report.id] = report
        DriftDetected(
            report_id=report.id,
            resource_id=resource_id,
            baseline_id=baseline_id,
            current_id=current_id,
            differences_count=len(differences),
            severity=severity,
        )
        self._log.info(
            "configdrift.drift.detected",
            report_id=report.id,
            resource=resource_id,
            changes=len(differences),
        )
        return report

    async def get_drift_reports(
        self,
        resource_id: str | None = None,
    ) -> list[DriftReport]:
        if resource_id is not None:
            return [r for r in self._reports.values() if r.resource_id == resource_id]
        return list(self._reports.values())

    async def resolve_drift(self, report_id: str) -> DriftReport:
        report = self._reports.get(report_id)
        if report is None:
            raise SnapshotNotFoundError(f"Drift report '{report_id}' not found")
        report = report.model_copy(
            update={"resolved": True, "resolved_at": utc_now()},
            deep=True,
        )
        self._reports[report_id] = report
        DriftResolved(report_id=report_id, resource_id=report.resource_id)
        self._log.info("configdrift.drift.resolved", report_id=report_id)
        return report

    async def set_baseline(self, resource_id: str, snapshot_id: str) -> None:
        if snapshot_id not in self._snapshots:
            raise SnapshotNotFoundError(f"Snapshot '{snapshot_id}' not found")
        self._baselines[resource_id] = snapshot_id
        self._log.info(
            "configdrift.baseline.set",
            resource=resource_id,
            snapshot=snapshot_id,
        )


__all__ = ["DriftDetector"]
