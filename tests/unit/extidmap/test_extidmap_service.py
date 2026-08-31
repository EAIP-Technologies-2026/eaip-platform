"""Tests for ExternalIdentityMapper."""

from __future__ import annotations

import pytest

from eaip.extidmap.exceptions import MappingNotFoundError
from eaip.extidmap.mapper import ExternalIdentityMapper
from eaip.extidmap.models import IdentityMapping, MapperConfig, MappingRule, MappingStatus


class TestExternalIdentityMapper:
    @pytest.fixture
    def mapper(self) -> ExternalIdentityMapper:
        return ExternalIdentityMapper()

    @pytest.fixture
    def sample_mapping(self) -> IdentityMapping:
        return IdentityMapping(
            id="m1",
            local_uid="user-1",
            external_uid="ext-user-1",
            external_idp="azure_ad",
            attributes={"email": "user1@example.com"},
            status=MappingStatus.ACTIVE,
        )

    class TestAddMapping:
        async def test_adds_mapping(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            result = await mapper.add_mapping(sample_mapping)
            assert result.id == "m1"
            assert result.local_uid == "user-1"

        async def test_stores_mapping(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            await mapper.add_mapping(sample_mapping)
            stored = await mapper.get_mapping("m1")
            assert stored.external_idp == "azure_ad"

    class TestGetMapping:
        async def test_returns_mapping(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            await mapper.add_mapping(sample_mapping)
            result = await mapper.get_mapping("m1")
            assert result.external_uid == "ext-user-1"

        async def test_raises_on_missing(self, mapper: ExternalIdentityMapper) -> None:
            with pytest.raises(MappingNotFoundError):
                await mapper.get_mapping("nonexistent")

    class TestUpdateMapping:
        async def test_updates_mapping(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            await mapper.add_mapping(sample_mapping)
            updated = await mapper.update_mapping("m1", external_uid="ext-user-2")
            assert updated.external_uid == "ext-user-2"

    class TestUnlinkMapping:
        async def test_revokes_mapping(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            await mapper.add_mapping(sample_mapping)
            await mapper.unlink_mapping("m1")
            stored = await mapper.get_mapping("m1")
            assert stored.status is MappingStatus.REVOKED

    class TestFindByLocal:
        async def test_finds_mappings(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            await mapper.add_mapping(sample_mapping)
            results = await mapper.find_by_local("user-1")
            assert len(results) == 1

        async def test_excludes_revoked(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            await mapper.add_mapping(sample_mapping)
            await mapper.unlink_mapping("m1")
            results = await mapper.find_by_local("user-1")
            assert len(results) == 0

    class TestAddRule:
        async def test_adds_rule(self, mapper: ExternalIdentityMapper) -> None:
            rule = MappingRule(
                id="r1",
                name="email_map",
                source_field="mail",
                target_field="email",
                transformation="direct",
            )
            result = await mapper.add_rule(rule)
            assert result.id == "r1"

        async def test_lists_rules(self, mapper: ExternalIdentityMapper) -> None:
            rule = MappingRule(
                id="r1",
                name="email_map",
                source_field="mail",
                target_field="email",
                transformation="direct",
            )
            await mapper.add_rule(rule)
            rules = await mapper.list_rules()
            assert len(rules) == 1

    class TestRefreshStaleMappings:
        async def test_marks_stale(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            await mapper.add_mapping(sample_mapping)
            count = await mapper.refresh_stale_mappings()
            assert count == 0

    class TestGetStatistics:
        async def test_returns_stats(
            self, mapper: ExternalIdentityMapper, sample_mapping: IdentityMapping
        ) -> None:
            await mapper.add_mapping(sample_mapping)
            stats = await mapper.get_statistics()
            assert stats["total_mappings"] == 1
            assert stats["active"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            m = ExternalIdentityMapper()
            assert m.config.default_idp == "azure_ad"

        def test_custom_config(self) -> None:
            cfg = MapperConfig(default_idp="okta")
            m = ExternalIdentityMapper(config=cfg)
            assert m.config.default_idp == "okta"
