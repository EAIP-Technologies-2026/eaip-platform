"""Legal hold service — create, manage, release, and check legal holds on data."""

from __future__ import annotations

from datetime import UTC, datetime

from eaip.audit.exceptions import LegalHoldError
from eaip.audit.models import LegalHold, LegalHoldStatus
from eaip.logging.context import get_logger


class LegalHoldService:
    def __init__(self) -> None:
        self._holds: dict[str, LegalHold] = {}
        self._log = get_logger("eaip.audit.legal_hold")

    def create_hold(
        self,
        hold: LegalHold,
    ) -> LegalHold:
        self._holds[hold.id] = hold
        self._log.info("audit.legal_hold.created", hold_id=hold.id, name=hold.name)
        return hold

    def get_hold(self, hold_id: str) -> LegalHold:
        hold = self._holds.get(hold_id)
        if hold is None:
            raise LegalHoldError(f"Legal hold {hold_id!r} not found")
        return hold

    def release_hold(self, hold_id: str, reason: str = "") -> LegalHold:
        hold = self.get_hold(hold_id)
        if hold.status != LegalHoldStatus.ACTIVE:
            raise LegalHoldError(f"Legal hold {hold_id!r} is not active (status={hold.status})")
        updated = hold.model_copy(
            update={"status": LegalHoldStatus.RELEASED, "end_date": datetime.now(UTC)}
        )
        self._holds[hold_id] = updated
        self._log.info("audit.legal_hold.released", hold_id=hold_id, reason=reason)
        return updated

    def list_active_holds(self) -> list[LegalHold]:
        now = datetime.now(UTC)
        active: list[LegalHold] = []
        for hold in self._holds.values():
            if hold.status == LegalHoldStatus.ACTIVE:
                if hold.end_date and hold.end_date <= now:
                    expired = hold.model_copy(update={"status": LegalHoldStatus.EXPIRED})
                    self._holds[hold.id] = expired
                    continue
                active.append(hold)
        return active

    async def check_hold(self, data_type: str, resource_id: str) -> bool:
        for hold in self._holds.values():
            if hold.status != LegalHoldStatus.ACTIVE:
                continue
            if data_type in hold.affected_data_types:
                return True
            if resource_id in hold.affected_resources:
                return True
        return False

    async def get_held_data_types(self) -> list[str]:
        data_types: set[str] = set()
        for hold in self._holds.values():
            if hold.status == LegalHoldStatus.ACTIVE:
                data_types.update(hold.affected_data_types)
        return sorted(data_types)


__all__ = ["LegalHoldService"]
