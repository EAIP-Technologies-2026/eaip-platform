"""Tests for ExportComplianceChecker."""

from __future__ import annotations

import pytest

from eaip.exportcheck.checker import ExportComplianceChecker
from eaip.exportcheck.exceptions import PartyNotFoundError
from eaip.exportcheck.models import ComplianceConfig, RestrictedParty, ScreeningStatus


class TestExportComplianceChecker:
    @pytest.fixture
    def checker(self) -> ExportComplianceChecker:
        return ExportComplianceChecker()

    @pytest.fixture
    def sample_party(self) -> RestrictedParty:
        return RestrictedParty(
            id="p1",
            name="Bad Actor Corp",
            aliases=("Bad Actor Ltd",),
            country="RU",
            list_type="sdn",
            sanctions=("uk", "us"),
        )

    class TestAddRestrictedParty:
        async def test_adds_party(
            self, checker: ExportComplianceChecker, sample_party: RestrictedParty
        ) -> None:
            result = await checker.add_restricted_party(sample_party)
            assert result.id == "p1"
            assert result.name == "Bad Actor Corp"

        async def test_stores_party(
            self, checker: ExportComplianceChecker, sample_party: RestrictedParty
        ) -> None:
            await checker.add_restricted_party(sample_party)
            stored = await checker.get_restricted_party("p1")
            assert stored.country == "RU"

    class TestGetRestrictedParty:
        async def test_returns_party(
            self, checker: ExportComplianceChecker, sample_party: RestrictedParty
        ) -> None:
            await checker.add_restricted_party(sample_party)
            result = await checker.get_restricted_party("p1")
            assert result.list_type == "sdn"

        async def test_raises_on_missing(self, checker: ExportComplianceChecker) -> None:
            with pytest.raises(PartyNotFoundError):
                await checker.get_restricted_party("nonexistent")

    class TestListRestrictedParties:
        async def test_empty_when_none(self, checker: ExportComplianceChecker) -> None:
            assert await checker.list_restricted_parties() == []

        async def test_filters_by_list_type(
            self, checker: ExportComplianceChecker, sample_party: RestrictedParty
        ) -> None:
            p2 = RestrictedParty(id="p2", name="Other Entity", list_type="eu")
            await checker.add_restricted_party(sample_party)
            await checker.add_restricted_party(p2)
            result = await checker.list_restricted_parties(list_type="sdn")
            assert len(result) == 1
            assert result[0].id == "p1"

    class TestScreenParty:
        async def test_clear_when_no_match(self, checker: ExportComplianceChecker) -> None:
            result = await checker.screen_party("Clean Company")
            assert result.status is ScreeningStatus.CLEAR
            assert result.match_score == 0.0

        async def test_blocked_on_exact_match(
            self, checker: ExportComplianceChecker, sample_party: RestrictedParty
        ) -> None:
            await checker.add_restricted_party(sample_party)
            result = await checker.screen_party("Bad Actor Corp")
            assert result.status is ScreeningStatus.BLOCKED
            assert result.match_score == 1.0

        async def test_flagged_on_partial_match(
            self, checker: ExportComplianceChecker, sample_party: RestrictedParty
        ) -> None:
            cfg = ComplianceConfig(min_match_score=0.3, auto_block_above=0.99)
            checker_with_cfg = ExportComplianceChecker(config=cfg)
            await checker_with_cfg.add_restricted_party(sample_party)
            result = await checker_with_cfg.screen_party("Bad Actor")
            assert result.status is ScreeningStatus.FLAGGED

        async def test_stores_screening_result(self, checker: ExportComplianceChecker) -> None:
            result = await checker.screen_party("Test Corp")
            stored = await checker.get_screening_result(result.id)
            assert stored.party_name == "Test Corp"

    class TestGetStatistics:
        async def test_returns_stats(
            self, checker: ExportComplianceChecker, sample_party: RestrictedParty
        ) -> None:
            await checker.add_restricted_party(sample_party)
            await checker.screen_party("Bad Actor Corp")
            await checker.screen_party("Good Corp")
            stats = await checker.get_statistics()
            assert stats["total_parties"] == 1
            assert stats["total_screenings"] == 2

    class TestConfig:
        def test_default_config(self) -> None:
            c = ExportComplianceChecker()
            assert c.config.min_match_score == 0.8

        def test_custom_config(self) -> None:
            cfg = ComplianceConfig(min_match_score=0.5)
            c = ExportComplianceChecker(config=cfg)
            assert c.config.min_match_score == 0.5
