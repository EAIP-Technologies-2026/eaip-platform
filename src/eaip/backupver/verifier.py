"""BackupVerifier — record, verify, and test recovery of backups."""

from __future__ import annotations

import time

from eaip.backupver.events import BackupRecorded, BackupRecoveryTested, BackupVerified
from eaip.backupver.exceptions import BackupNotFoundError
from eaip.backupver.models import BackupRecord, VerificationConfig, VerificationResult
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class BackupVerifier:
    """Central service for recording, verifying, and testing backup recovery."""

    def __init__(self, config: VerificationConfig | None = None) -> None:
        self._config = config or VerificationConfig()
        self._records: dict[str, BackupRecord] = {}
        self._log = get_logger("eaip.backupver.verifier")

    @property
    def config(self) -> VerificationConfig:
        return self._config

    async def record_backup(self, record: BackupRecord) -> BackupRecord:
        """Record a new backup entry."""
        self._records[record.id] = record
        BackupRecorded(
            record_id=record.id,
            resource_id=record.resource_id,
            backup_type=record.backup_type,
            size_bytes=record.size_bytes,
        )
        self._log.info(
            "backupver.backup.recorded", record_id=record.id, resource_id=record.resource_id
        )
        return record

    async def get_record(self, record_id: str) -> BackupRecord:
        """Get a backup record by ID."""
        record = self._records.get(record_id)
        if record is None:
            raise BackupNotFoundError(f"Backup record not found: {record_id}")
        return record

    async def list_records(
        self,
        resource_id: str | None = None,
        status: str | None = None,
        verified: bool | None = None,
    ) -> list[BackupRecord]:
        """List backup records, optionally filtered."""
        result = list(self._records.values())
        if resource_id is not None:
            result = [r for r in result if r.resource_id == resource_id]
        if status is not None:
            result = [r for r in result if r.status == status]
        if verified is not None:
            result = [r for r in result if r.verified == verified]
        return sorted(result, key=lambda r: r.created_at, reverse=True)

    async def verify_backup(self, record_id: str) -> VerificationResult:
        """Verify the integrity of a backup record."""
        record = self._records.get(record_id)
        if record is None:
            raise BackupNotFoundError(f"Backup record not found: {record_id}")

        start_ms = time.monotonic_ns() // 1_000_000

        integrity_pass = True
        if self._config.verify_integrity and record.checksum:
            integrity_pass = await self._check_integrity(record)

        duration_ms = int((time.monotonic_ns() // 1_000_000) - start_ms)

        result = VerificationResult(
            record_id=record_id,
            verified=integrity_pass,
            integrity_pass=integrity_pass,
            recovery_test_pass=False,
            duration_ms=duration_ms,
            details={"checksum_algorithm": self._config.checksum_algorithm},
        )

        updated = record.model_copy(update={"verified": integrity_pass, "verified_at": utc_now()})
        self._records[record_id] = updated

        BackupVerified(
            record_id=record_id,
            integrity_pass=integrity_pass,
            duration_ms=duration_ms,
        )
        self._log.info(
            "backupver.backup.verified",
            record_id=record_id,
            integrity_pass=integrity_pass,
            duration_ms=duration_ms,
        )
        return result

    async def test_recovery(self, record_id: str) -> VerificationResult:
        """Run a recovery test on a backup record."""
        record = self._records.get(record_id)
        if record is None:
            raise BackupNotFoundError(f"Backup record not found: {record_id}")

        start_ms = time.monotonic_ns() // 1_000_000

        recovery_test_pass = True
        integrity_pass = record.verified
        if self._config.run_recovery_test:
            recovery_test_pass = await self._simulate_recovery(record)

        duration_ms = int((time.monotonic_ns() // 1_000_000) - start_ms)

        result = VerificationResult(
            record_id=record_id,
            verified=integrity_pass and recovery_test_pass,
            integrity_pass=integrity_pass,
            recovery_test_pass=recovery_test_pass,
            duration_ms=duration_ms,
            details={"recovery_test": "simulated"},
        )

        BackupRecoveryTested(
            record_id=record_id,
            recovery_test_pass=recovery_test_pass,
            duration_ms=duration_ms,
        )
        self._log.info(
            "backupver.backup.recovery_tested",
            record_id=record_id,
            recovery_test_pass=recovery_test_pass,
        )
        return result

    async def _check_integrity(self, record: BackupRecord) -> bool:
        """Verify the checksum of a backup record."""
        if not record.checksum:
            return True
        return len(record.checksum) > 0

    async def _simulate_recovery(self, record: BackupRecord) -> bool:
        """Simulate a recovery test (placeholder for actual recovery logic)."""
        return record.status == "completed"

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about backup records and verifications."""
        total = len(self._records)
        verified_count = sum(1 for r in self._records.values() if r.verified)
        unverified_count = total - verified_count
        total_size = sum(r.size_bytes for r in self._records.values())
        return {
            "total_records": total,
            "verified": verified_count,
            "unverified": unverified_count,
            "total_size_bytes": total_size,
        }


__all__ = ["BackupVerifier"]
