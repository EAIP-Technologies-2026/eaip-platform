"""Tests for DriftDetector."""

from __future__ import annotations

import pytest

from eaip.configdrift.detector import DriftDetector
from eaip.configdrift.exceptions import (
    DriftDetectionError,
    SnapshotNotFoundError,
)
from eaip.configdrift.models import DriftConfig


class TestDriftDetector:
    @pytest.fixture
    def detector(self) -> DriftDetector:
        return DriftDetector()

    class TestCaptureSnapshot:
        async def test_capture(self, detector: DriftDetector) -> None:
            snap = await detector.capture_snapshot("res1", {"key": "value"}, snapshot_id="s1")
            assert snap.id == "s1"
            assert snap.resource_id == "res1"
            assert snap.checksum != ""

        async def test_auto_id(self, detector: DriftDetector) -> None:
            snap = await detector.capture_snapshot("res1", {"key": "value"})
            assert snap.id.startswith("snap_")

    class TestGetSnapshot:
        async def test_get(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"key": "val"}, snapshot_id="s1")
            snap = await detector.get_snapshot("s1")
            assert snap.resource_id == "res1"

        async def test_not_found(self, detector: DriftDetector) -> None:
            with pytest.raises(SnapshotNotFoundError):
                await detector.get_snapshot("nonexistent")

    class TestListSnapshots:
        async def test_list_all(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"a": 1}, snapshot_id="s1")
            await detector.capture_snapshot("res2", {"b": 2}, snapshot_id="s2")
            snaps = await detector.list_snapshots()
            assert len(snaps) == 2

        async def test_list_by_resource(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"a": 1}, snapshot_id="s1")
            await detector.capture_snapshot("res1", {"a": 2}, snapshot_id="s2")
            snaps = await detector.list_snapshots(resource_id="res1")
            assert len(snaps) == 2

    class TestCompareSnapshots:
        async def test_identical(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"key": "val"}, snapshot_id="s1")
            await detector.capture_snapshot("res1", {"key": "val"}, snapshot_id="s2")
            diffs = await detector.compare_snapshots("s1", "s2")
            assert len(diffs) == 0

        async def test_different(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"key": "old"}, snapshot_id="s1")
            await detector.capture_snapshot("res1", {"key": "new"}, snapshot_id="s2")
            diffs = await detector.compare_snapshots("s1", "s2")
            assert len(diffs) == 1
            assert diffs[0]["path"] == "key"

        async def test_added_key(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"a": 1}, snapshot_id="s1")
            await detector.capture_snapshot("res1", {"a": 1, "b": 2}, snapshot_id="s2")
            diffs = await detector.compare_snapshots("s1", "s2")
            assert len(diffs) == 1
            assert diffs[0]["added"] is True

    class TestDetectDrift:
        async def test_detect(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"key": "old"}, snapshot_id="s1")
            await detector.set_baseline("res1", "s1")
            await detector.capture_snapshot("res1", {"key": "new"}, snapshot_id="s2")
            report = await detector.detect_drift("res1", "s2")
            assert len(report.differences) == 1
            assert report.resource_id == "res1"

        async def test_no_baseline(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"key": "val"}, snapshot_id="s1")
            with pytest.raises(DriftDetectionError):
                await detector.detect_drift("res1", "s1")

    class TestDriftReports:
        async def test_get_reports(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"k": "old"}, snapshot_id="s1")
            await detector.set_baseline("res1", "s1")
            await detector.capture_snapshot("res1", {"k": "new"}, snapshot_id="s2")
            await detector.detect_drift("res1", "s2")
            reports = await detector.get_drift_reports()
            assert len(reports) == 1

        async def test_get_reports_by_resource(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"k": "old"}, snapshot_id="s1")
            await detector.set_baseline("res1", "s1")
            await detector.capture_snapshot("res1", {"k": "new"}, snapshot_id="s2")
            await detector.detect_drift("res1", "s2")
            reports = await detector.get_drift_reports(resource_id="res1")
            assert len(reports) == 1

    class TestResolveDrift:
        async def test_resolve(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"k": "old"}, snapshot_id="s1")
            await detector.set_baseline("res1", "s1")
            await detector.capture_snapshot("res1", {"k": "new"}, snapshot_id="s2")
            report = await detector.detect_drift("res1", "s2")
            resolved = await detector.resolve_drift(report.id)
            assert resolved.resolved is True
            assert resolved.resolved_at is not None

        async def test_resolve_not_found(self, detector: DriftDetector) -> None:
            with pytest.raises(SnapshotNotFoundError):
                await detector.resolve_drift("nonexistent")

    class TestSetBaseline:
        async def test_set_baseline(self, detector: DriftDetector) -> None:
            await detector.capture_snapshot("res1", {"k": "v"}, snapshot_id="s1")
            await detector.set_baseline("res1", "s1")
            await detector.capture_snapshot("res1", {"k": "v2"}, snapshot_id="s2")
            report = await detector.detect_drift("res1", "s2")
            assert report.baseline_id == "s1"

        async def test_set_baseline_not_found(self, detector: DriftDetector) -> None:
            with pytest.raises(SnapshotNotFoundError):
                await detector.set_baseline("res1", "nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            d = DriftDetector()
            assert d.config.scan_interval_minutes == 60
            assert d.config.default_severity == "warning"

        def test_custom_config(self) -> None:
            config = DriftConfig(scan_interval_minutes=30, default_severity="critical")
            d = DriftDetector(config=config)
            assert d.config.scan_interval_minutes == 30
            assert d.config.default_severity == "critical"

    class TestChecksum:
        async def test_checksum_consistency(self, detector: DriftDetector) -> None:
            s1 = await detector.capture_snapshot("r1", {"a": 1, "b": 2})
            s2 = await detector.capture_snapshot("r1", {"b": 2, "a": 1})
            assert s1.checksum == s2.checksum

        async def test_checksum_different(self, detector: DriftDetector) -> None:
            s1 = await detector.capture_snapshot("r1", {"a": 1})
            s2 = await detector.capture_snapshot("r1", {"a": 2})
            assert s1.checksum != s2.checksum
