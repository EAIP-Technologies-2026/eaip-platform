"""ExportComplianceChecker — screen parties against restricted lists."""

from __future__ import annotations

from eaip.exportcheck.events import MatchFlagged, PartyScreened, RuleUpdated
from eaip.exportcheck.exceptions import PartyNotFoundError
from eaip.exportcheck.models import (
    ComplianceConfig,
    RestrictedParty,
    ScreeningResult,
    ScreeningStatus,
)
from eaip.logging.context import get_logger


class ExportComplianceChecker:
    """Central service for screening parties against restricted lists."""

    def __init__(self, config: ComplianceConfig | None = None) -> None:
        self._config = config or ComplianceConfig()
        self._parties: dict[str, RestrictedParty] = {}
        self._results: dict[str, ScreeningResult] = {}
        self._log = get_logger("eaip.exportcheck.checker")

    @property
    def config(self) -> ComplianceConfig:
        return self._config

    async def add_restricted_party(self, party: RestrictedParty) -> RestrictedParty:
        """Add a restricted party to the watch list."""
        self._parties[party.id] = party
        RuleUpdated(
            rule_id=party.id,
            list_type=party.list_type,
            action="added",
        )
        self._log.info("exportcheck.party.added", party_id=party.id, name=party.name)
        return party

    async def get_restricted_party(self, party_id: str) -> RestrictedParty:
        """Get a restricted party by ID."""
        party = self._parties.get(party_id)
        if party is None:
            raise PartyNotFoundError(f"Restricted party not found: {party_id}")
        return party

    async def list_restricted_parties(self, list_type: str | None = None) -> list[RestrictedParty]:
        """List restricted parties, optionally filtered by list type."""
        result = list(self._parties.values())
        if list_type is not None:
            result = [p for p in result if p.list_type == list_type]
        return sorted(result, key=lambda p: p.added_at, reverse=True)

    async def screen_party(self, party_name: str) -> ScreeningResult:
        """Screen a party name against the restricted list."""
        matches: list[tuple[str, float]] = []
        for party in self._parties.values():
            score = await self._compute_match_score(party_name, party)
            if score > 0:
                matches.append((party.list_type, score))

        if not matches:
            result = ScreeningResult(
                id=f"scr-{len(self._results) + 1}",
                party_name=party_name,
                match_score=0.0,
                status=ScreeningStatus.CLEAR,
            )
        else:
            max_score = max(s for _, s in matches)
            matched = tuple(m for m, _ in matches)
            if max_score >= self._config.auto_block_above:
                status = ScreeningStatus.BLOCKED
            elif max_score >= self._config.min_match_score:
                status = ScreeningStatus.FLAGGED
            else:
                status = ScreeningStatus.CLEAR

            result = ScreeningResult(
                id=f"scr-{len(self._results) + 1}",
                party_name=party_name,
                match_score=max_score,
                matched_rules=matched,
                status=status,
            )

            if status is ScreeningStatus.FLAGGED:
                MatchFlagged(
                    party_name=party_name,
                    match_score=max_score,
                    matched_list=matched[0] if matched else "",
                )

        self._results[result.id] = result
        PartyScreened(
            party_name=party_name,
            match_score=result.match_score,
            status=result.status,
        )
        self._log.info(
            "exportcheck.party.screened",
            party_name=party_name,
            status=result.status.value,
        )
        return result

    async def get_screening_result(self, result_id: str) -> ScreeningResult:
        """Get a screening result by ID."""
        result = self._results.get(result_id)
        if result is None:
            raise PartyNotFoundError(f"Screening result not found: {result_id}")
        return result

    async def _compute_match_score(self, party_name: str, party: RestrictedParty) -> float:
        """Compute a match score between a party name and a restricted party."""
        name_lower = party_name.lower()
        if name_lower == party.name.lower():
            return 1.0
        for alias in party.aliases:
            if name_lower == alias.lower():
                return 0.95
        words = set(name_lower.split())
        party_words = set(party.name.lower().split())
        if words and party_words:
            intersection = words & party_words
            return len(intersection) / max(len(words), len(party_words))
        return 0.0

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about screening."""
        return {
            "total_parties": len(self._parties),
            "total_screenings": len(self._results),
            "flagged": sum(
                1 for r in self._results.values() if r.status is ScreeningStatus.FLAGGED
            ),
            "blocked": sum(
                1 for r in self._results.values() if r.status is ScreeningStatus.BLOCKED
            ),
            "cleared": sum(1 for r in self._results.values() if r.status is ScreeningStatus.CLEAR),
        }


__all__ = ["ExportComplianceChecker"]
