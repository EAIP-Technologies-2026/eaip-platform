"""FileIntegrityMonitor — record baselines and verify file integrity."""

from __future__ import annotations

from eaip.fileintmon.events import BaselineRecorded, IntegrityVerified, IntegrityViolation
from eaip.fileintmon.exceptions import FileNotFoundError
from eaip.fileintmon.models import (
    FileStatus,
    IntegrityCheck,
    MonitorConfig,
    MonitoredFile,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class FileIntegrityMonitor:
    """Central service for monitoring file integrity via checksums."""

    def __init__(self, config: MonitorConfig | None = None) -> None:
        self._config = config or MonitorConfig()
        self._files: dict[str, MonitoredFile] = {}
        self._checks: dict[str, IntegrityCheck] = {}
        self._log = get_logger("eaip.fileintmon.monitor")

    @property
    def config(self) -> MonitorConfig:
        return self._config

    async def record_baseline(self, monitored_file: MonitoredFile) -> MonitoredFile:
        """Record a baseline hash for a monitored file."""
        self._files[monitored_file.id] = monitored_file
        BaselineRecorded(
            file_id=monitored_file.id,
            path=monitored_file.path,
            hash_value=monitored_file.baseline_hash,
            algorithm=monitored_file.checksum_algorithm,
        )
        self._log.info(
            "fileintmon.baseline.recorded",
            file_id=monitored_file.id,
            path=monitored_file.path,
        )
        return monitored_file

    async def get_monitored_file(self, file_id: str) -> MonitoredFile:
        """Get a monitored file by ID."""
        mf = self._files.get(file_id)
        if mf is None:
            raise FileNotFoundError(f"Monitored file not found: {file_id}")
        return mf

    async def list_monitored_files(self, status: FileStatus | None = None) -> list[MonitoredFile]:
        """List monitored files, optionally filtered by status."""
        result = list(self._files.values())
        if status is not None:
            result = [f for f in result if f.status == status]
        return sorted(result, key=lambda f: f.path)

    async def verify_integrity(self, file_id: str, actual_hash: str) -> IntegrityCheck:
        """Verify the integrity of a monitored file against its baseline."""
        mf = await self.get_monitored_file(file_id)

        match = mf.baseline_hash == actual_hash
        check = IntegrityCheck(
            id=f"chk-{len(self._checks) + 1}",
            file_id=file_id,
            expected_hash=mf.baseline_hash,
            actual_hash=actual_hash,
            match=match,
        )
        self._checks[check.id] = check

        updated_status = mf.status
        if not match:
            updated_status = FileStatus.CHANGED
            IntegrityViolation(
                file_id=file_id,
                path=mf.path,
                expected_hash=mf.baseline_hash,
                actual_hash=actual_hash,
                reason="hash_mismatch",
            )

        updated = mf.model_copy(
            update={
                "last_verified_at": utc_now(),
                "status": updated_status,
            }
        )
        self._files[file_id] = updated

        IntegrityVerified(
            file_id=file_id,
            path=mf.path,
            hash_matched=match,
        )
        self._log.info(
            "fileintmon.integrity.verified",
            file_id=file_id,
            match=match,
        )
        return check

    async def mark_deleted(self, file_id: str) -> MonitoredFile:
        """Mark a monitored file as deleted."""
        mf = await self.get_monitored_file(file_id)
        updated = mf.model_copy(update={"status": FileStatus.DELETED})
        self._files[file_id] = updated
        IntegrityViolation(
            file_id=file_id,
            path=mf.path,
            expected_hash=mf.baseline_hash,
            actual_hash="",
            reason="file_deleted",
        )
        self._log.warning("fileintmon.file.deleted", file_id=file_id, path=mf.path)
        return updated

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about integrity monitoring."""
        total = len(self._files)
        baseline = sum(1 for f in self._files.values() if f.status is FileStatus.BASELINE)
        changed = sum(1 for f in self._files.values() if f.status is FileStatus.CHANGED)
        deleted = sum(1 for f in self._files.values() if f.status is FileStatus.DELETED)
        total_checks = len(self._checks)
        passed = sum(1 for c in self._checks.values() if c.match)
        failed = total_checks - passed
        return {
            "total_files": total,
            "baseline": baseline,
            "changed": changed,
            "deleted": deleted,
            "total_checks": total_checks,
            "checks_passed": passed,
            "checks_failed": failed,
        }


__all__ = ["FileIntegrityMonitor"]
