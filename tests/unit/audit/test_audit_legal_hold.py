"""Tests for LegalHoldService."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from eaip.audit.exceptions import LegalHoldError
from eaip.audit.legal_hold import LegalHoldService
from eaip.audit.models import LegalHold, LegalHoldStatus


class TestLegalHoldService:
    def test_create_hold(self) -> None:
        service = LegalHoldService()
        hold = LegalHold(id="lh1", name="Investigation", reason="Legal case")
        result = service.create_hold(hold)
        assert result.id == "lh1"
        assert result.status == LegalHoldStatus.ACTIVE

    def test_get_hold(self) -> None:
        service = LegalHoldService()
        hold = LegalHold(id="lh1", name="Hold1", reason="Test")
        service.create_hold(hold)
        result = service.get_hold("lh1")
        assert result.name == "Hold1"

    def test_get_hold_not_found(self) -> None:
        service = LegalHoldService()
        with pytest.raises(LegalHoldError):
            service.get_hold("nonexistent")

    def test_release_hold(self) -> None:
        service = LegalHoldService()
        hold = LegalHold(id="lh1", name="Hold1", reason="Test")
        service.create_hold(hold)
        released = service.release_hold("lh1", reason="Case closed")
        assert released.status == LegalHoldStatus.RELEASED
        assert released.end_date is not None

    def test_release_hold_already_released(self) -> None:
        service = LegalHoldService()
        hold = LegalHold(id="lh1", name="Hold1", reason="Test")
        service.create_hold(hold)
        service.release_hold("lh1")
        with pytest.raises(LegalHoldError):
            service.release_hold("lh1")

    def test_release_hold_not_found(self) -> None:
        service = LegalHoldService()
        with pytest.raises(LegalHoldError):
            service.release_hold("nonexistent")

    def test_list_active_holds(self) -> None:
        service = LegalHoldService()
        service.create_hold(LegalHold(id="lh1", name="Active1", reason="R1"))
        service.create_hold(LegalHold(id="lh2", name="Active2", reason="R2"))
        service.create_hold(
            LegalHold(id="lh3", name="Released", reason="R3", status=LegalHoldStatus.RELEASED)
        )
        active = service.list_active_holds()
        assert len(active) == 2
        assert {h.id for h in active} == {"lh1", "lh2"}

    def test_list_active_holds_expired(self) -> None:
        service = LegalHoldService()
        past = datetime.now(UTC) - timedelta(days=1)
        expired_hold = LegalHold(
            id="lh1", name="Expired", reason="R", end_date=past, status=LegalHoldStatus.ACTIVE
        )
        service.create_hold(expired_hold)
        active = service.list_active_holds()
        assert len(active) == 0
        stored = service.get_hold("lh1")
        assert stored.status == LegalHoldStatus.EXPIRED

    async def test_check_hold_matches_data_type(self) -> None:
        service = LegalHoldService()
        hold = LegalHold(
            id="lh1", name="Hold1", reason="R", affected_data_types=("pii", "financial")
        )
        service.create_hold(hold)
        result = await service.check_hold("pii", "res-1")
        assert result is True

    async def test_check_hold_matches_resource_id(self) -> None:
        service = LegalHoldService()
        hold = LegalHold(id="lh1", name="Hold1", reason="R", affected_resources=("doc-1", "doc-2"))
        service.create_hold(hold)
        result = await service.check_hold("logs", "doc-1")
        assert result is True

    async def test_check_hold_no_match(self) -> None:
        service = LegalHoldService()
        hold = LegalHold(
            id="lh1",
            name="Hold1",
            reason="R",
            affected_data_types=("pii",),
            affected_resources=("doc-1",),
        )
        service.create_hold(hold)
        result = await service.check_hold("logs", "doc-999")
        assert result is False

    async def test_check_hold_released(self) -> None:
        service = LegalHoldService()
        hold = LegalHold(
            id="lh1",
            name="Hold1",
            reason="R",
            affected_data_types=("pii",),
            status=LegalHoldStatus.RELEASED,
        )
        service.create_hold(hold)
        result = await service.check_hold("pii", "res-1")
        assert result is False

    async def test_get_held_data_types(self) -> None:
        service = LegalHoldService()
        service.create_hold(
            LegalHold(id="lh1", name="H1", reason="R", affected_data_types=("pii", "financial"))
        )
        service.create_hold(
            LegalHold(id="lh2", name="H2", reason="R", affected_data_types=("financial", "health"))
        )
        service.create_hold(
            LegalHold(
                id="lh3",
                name="H3",
                reason="R",
                affected_data_types=("logs",),
                status=LegalHoldStatus.RELEASED,
            )
        )
        data_types = await service.get_held_data_types()
        assert sorted(data_types) == ["financial", "health", "pii"]
