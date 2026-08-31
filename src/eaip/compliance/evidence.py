"""Evidence collection for compliance controls."""

from __future__ import annotations

import uuid
from typing import Any

from eaip.compliance.models import EvidenceRecord
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class EvidenceCollector:
    """Collects and validates evidence from various sources."""

    SOURCE_AUDIT = "audit"
    SOURCE_POLICY = "policy"
    SOURCE_DATAMASK = "datamask"

    def __init__(self) -> None:
        """Initialize the evidence collector."""
        self._log = get_logger("eaip.compliance.evidence")
        self._store: dict[str, EvidenceRecord] = {}

    async def collect(
        self,
        control_id: str,
        source: str,
        data: dict[str, Any] | None = None,
        collected_by: str | None = None,
    ) -> EvidenceRecord:
        """Collect evidence for a control from a given source."""
        record = EvidenceRecord(
            evidence_id=str(uuid.uuid4()),
            control_id=control_id,
            source=source,
            timestamp=utc_now(),
            data=data or {},
            collected_by=collected_by or "unknown",
            valid=True,
        )
        self._store[record.evidence_id] = record
        self._log.info(
            "evidence.collected",
            evidence_id=record.evidence_id,
            control_id=control_id,
            source=source,
        )
        return record

    async def collect_from_audit(
        self,
        control_id: str,
        data: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        """Collect evidence from an audit source."""
        return await self.collect(control_id, self.SOURCE_AUDIT, data, "evidence.audit")

    async def collect_from_policy(
        self,
        control_id: str,
        data: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        """Collect evidence from a policy source."""
        return await self.collect(control_id, self.SOURCE_POLICY, data, "evidence.policy")

    async def collect_from_datamask(
        self,
        control_id: str,
        data: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        """Collect evidence from a data masking source."""
        return await self.collect(control_id, self.SOURCE_DATAMASK, data, "evidence.datamask")

    def get_evidence(self, evidence_id: str) -> EvidenceRecord | None:
        """Get evidence by ID."""
        return self._store.get(evidence_id)

    def get_evidence_for_control(self, control_id: str) -> tuple[EvidenceRecord, ...]:
        """Get all evidence for a control."""
        return tuple(e for e in self._store.values() if e.control_id == control_id)

    def invalidate_evidence(self, evidence_id: str) -> EvidenceRecord | None:
        """Invalidate evidence by ID."""
        record = self._store.get(evidence_id)
        if record is None:
            return None

        updated = EvidenceRecord(
            evidence_id=record.evidence_id,
            control_id=record.control_id,
            source=record.source,
            timestamp=record.timestamp,
            data=record.data,
            collected_by=record.collected_by,
            valid=False,
        )
        self._store[evidence_id] = updated
        return updated

    def count(self) -> int:
        """Return the number of evidence records."""
        return len(self._store)

    def clear(self) -> None:
        """Clear all evidence records."""
        self._store.clear()
