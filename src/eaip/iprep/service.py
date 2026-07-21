"""IPReputationService — check, track, and manage IP address reputation."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from eaip.iprep.events import (
    BlocklistUpdated,
    IPChecked,
    ReputationChanged,
)
from eaip.iprep.exceptions import IPNotFoundError
from eaip.iprep.models import (
    IPCategory,
    IPReputation,
    ReputationCheck,
    ReputationConfig,
)
from eaip.shared.time import utc_now

EventCallback = Callable[[Any], Any]


class IPReputationService:
    def __init__(
        self,
        config: ReputationConfig | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self._config = config or ReputationConfig()
        self._reputations: dict[str, IPReputation] = {}
        self._checks: dict[str, ReputationCheck] = {}
        self._blocklist: set[str] = set()
        self._event_callback = event_callback

    def set_event_callback(self, callback: EventCallback | None) -> None:
        self._event_callback = callback

    def _emit(self, event: Any) -> None:
        if self._event_callback:
            self._event_callback(event)

    def _categorize(self, score: int) -> IPCategory:
        if score >= self._config.malicious_threshold:
            return IPCategory.MALICIOUS
        if score >= self._config.suspicious_threshold:
            return IPCategory.SUSPICIOUS
        return IPCategory.SAFE

    async def check_ip(self, ip: str) -> ReputationCheck:
        reputation = self._reputations.get(ip)
        score = reputation.score if reputation else 0

        check = ReputationCheck(
            id=str(uuid.uuid4()),
            ip=ip,
            score=score,
            action="allow" if score < self._config.malicious_threshold else "block",
        )
        self._checks[check.id] = check

        category = self._categorize(score)
        self._emit(IPChecked(ip=ip, score=score, category=category))
        return check

    async def get_reputation(self, ip: str) -> IPReputation:
        if ip not in self._reputations:
            raise IPNotFoundError(ip)
        return self._reputations[ip]

    async def update_reputation(
        self,
        ip: str,
        score: int,
        *,
        threat_type: str = "",
        source_feed: str = "",
    ) -> IPReputation:
        old = self._reputations.get(ip)
        old_score = old.score if old else 0
        old_category = old.category if old else IPCategory.SAFE

        now = utc_now()
        reputation = IPReputation(
            ip=ip,
            score=score,
            category=self._categorize(score),
            threat_type=threat_type,
            first_seen=old.first_seen if old else now,
            last_seen=now,
            source_feed=source_feed or (old.source_feed if old else ""),
        )
        self._reputations[ip] = reputation

        new_category = self._categorize(score)
        if new_category != old_category or abs(score - old_score) >= 10:
            self._emit(
                ReputationChanged(
                    ip=ip,
                    old_score=old_score,
                    new_score=score,
                    old_category=old_category,
                    new_category=new_category,
                )
            )

        if score >= self._config.malicious_threshold and self._config.enable_auto_blocklist:
            if ip not in self._blocklist:
                self._blocklist.add(ip)
                self._emit(
                    BlocklistUpdated(
                        ip=ip,
                        reason=f"Score {score} exceeds malicious threshold",
                        entries_count=len(self._blocklist),
                    )
                )

        return reputation

    async def list_blocklist(self) -> list[IPReputation]:
        return [r for ip, r in self._reputations.items() if ip in self._blocklist]

    async def remove_from_blocklist(self, ip: str) -> bool:
        if ip in self._blocklist:
            self._blocklist.discard(ip)
            return True
        return False


__all__ = ["IPReputationService"]
