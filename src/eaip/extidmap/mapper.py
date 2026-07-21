"""ExternalIdentityMapper — map identities between local and external systems."""

from __future__ import annotations

from datetime import timedelta

from eaip.extidmap.events import IdentityMapped, IdentityUnlinked, MappingUpdated
from eaip.extidmap.exceptions import MappingNotFoundError
from eaip.extidmap.models import (
    IdentityMapping,
    MapperConfig,
    MappingRule,
    MappingStatus,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class ExternalIdentityMapper:
    """Central service for mapping local identities to external identity providers."""

    def __init__(self, config: MapperConfig | None = None) -> None:
        self._config = config or MapperConfig()
        self._mappings: dict[str, IdentityMapping] = {}
        self._rules: dict[str, MappingRule] = {}
        self._log = get_logger("eaip.extidmap.mapper")

    @property
    def config(self) -> MapperConfig:
        return self._config

    async def add_mapping(self, mapping: IdentityMapping) -> IdentityMapping:
        """Add a new identity mapping."""
        self._mappings[mapping.id] = mapping
        IdentityMapped(
            local_uid=mapping.local_uid,
            external_uid=mapping.external_uid,
            external_idp=mapping.external_idp,
        )
        self._log.info(
            "extidmap.mapping.added",
            mapping_id=mapping.id,
            local_uid=mapping.local_uid,
        )
        return mapping

    async def get_mapping(self, mapping_id: str) -> IdentityMapping:
        """Get an identity mapping by ID."""
        mapping = self._mappings.get(mapping_id)
        if mapping is None:
            raise MappingNotFoundError(f"Identity mapping not found: {mapping_id}")
        return mapping

    async def update_mapping(self, mapping_id: str, **updates: object) -> IdentityMapping:
        """Update an identity mapping."""
        existing = await self.get_mapping(mapping_id)
        updated = existing.model_copy(update=updates)
        self._mappings[mapping_id] = updated
        MappingUpdated(
            mapping_id=mapping_id,
            changes=dict(updates),
        )
        self._log.info("extidmap.mapping.updated", mapping_id=mapping_id)
        return updated

    async def unlink_mapping(self, mapping_id: str) -> None:
        """Revoke/unlink an identity mapping."""
        mapping = await self.get_mapping(mapping_id)
        updated = mapping.model_copy(update={"status": MappingStatus.REVOKED})
        self._mappings[mapping_id] = updated
        IdentityUnlinked(
            mapping_id=mapping_id,
            local_uid=mapping.local_uid,
            external_idp=mapping.external_idp,
        )
        self._log.info("extidmap.mapping.unlinked", mapping_id=mapping_id)

    async def find_by_local(self, local_uid: str) -> list[IdentityMapping]:
        """Find all mappings for a local identity."""
        return [
            m
            for m in self._mappings.values()
            if m.local_uid == local_uid and m.status is not MappingStatus.REVOKED
        ]

    async def find_by_external(
        self, external_uid: str, idp: str | None = None
    ) -> list[IdentityMapping]:
        """Find mappings for an external identity."""
        results = [
            m
            for m in self._mappings.values()
            if m.external_uid == external_uid and m.status is not MappingStatus.REVOKED
        ]
        if idp is not None:
            results = [m for m in results if m.external_idp == idp]
        return results

    async def add_rule(self, rule: MappingRule) -> MappingRule:
        """Add a mapping rule."""
        self._rules[rule.id] = rule
        self._log.info("extidmap.rule.added", rule_id=rule.id)
        return rule

    async def list_rules(self) -> list[MappingRule]:
        """List all mapping rules."""
        return list(self._rules.values())

    async def refresh_stale_mappings(self) -> int:
        """Mark mappings older than stale_after_days as STALE."""
        cutoff = utc_now() - timedelta(days=self._config.stale_after_days)
        stale_count = 0
        for m_id, mapping in list(self._mappings.items()):
            if mapping.mapped_at < cutoff and mapping.status is MappingStatus.ACTIVE:
                updated = mapping.model_copy(update={"status": MappingStatus.STALE})
                self._mappings[m_id] = updated
                stale_count += 1
        if stale_count:
            self._log.info("extidmap.mappings.stale", count=stale_count)
        return stale_count

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about identity mappings."""
        total = len(self._mappings)
        active = sum(1 for m in self._mappings.values() if m.status is MappingStatus.ACTIVE)
        stale = sum(1 for m in self._mappings.values() if m.status is MappingStatus.STALE)
        revoked = sum(1 for m in self._mappings.values() if m.status is MappingStatus.REVOKED)
        return {
            "total_mappings": total,
            "active": active,
            "stale": stale,
            "revoked": revoked,
            "total_rules": len(self._rules),
        }


__all__ = ["ExternalIdentityMapper"]
