"""Tests for FirewallRuleManager."""

from __future__ import annotations

import pytest

from eaip.firewall.exceptions import RuleNotFoundError
from eaip.firewall.manager import FirewallRuleManager
from eaip.firewall.models import (
    FirewallConfig,
    FirewallRule,
    RuleAction,
    RuleSet,
    RuleSetStatus,
)


class TestFirewallRuleManager:
    @pytest.fixture
    def manager(self) -> FirewallRuleManager:
        return FirewallRuleManager()

    @pytest.fixture
    def sample_rule(self) -> FirewallRule:
        return FirewallRule(
            id="r1",
            name="allow-http",
            source="10.0.0.0/8",
            destination="*",
            port=80,
            protocol="tcp",
            action=RuleAction.ALLOW,
            priority=100,
            enabled=True,
            environment="production",
        )

    class TestCreateRule:
        async def test_creates_rule(
            self, manager: FirewallRuleManager, sample_rule: FirewallRule
        ) -> None:
            result = await manager.create_rule(sample_rule)
            assert result.id == "r1"
            assert result.name == "allow-http"

        async def test_stores_rule(
            self, manager: FirewallRuleManager, sample_rule: FirewallRule
        ) -> None:
            await manager.create_rule(sample_rule)
            stored = await manager.get_rule("r1")
            assert stored.port == 80

    class TestGetRule:
        async def test_returns_rule(
            self, manager: FirewallRuleManager, sample_rule: FirewallRule
        ) -> None:
            await manager.create_rule(sample_rule)
            result = await manager.get_rule("r1")
            assert result.action is RuleAction.ALLOW

        async def test_raises_on_missing(self, manager: FirewallRuleManager) -> None:
            with pytest.raises(RuleNotFoundError):
                await manager.get_rule("nonexistent")

    class TestUpdateRule:
        async def test_updates_rule(
            self, manager: FirewallRuleManager, sample_rule: FirewallRule
        ) -> None:
            await manager.create_rule(sample_rule)
            updated = await manager.update_rule("r1", port=443)
            assert updated.port == 443

    class TestDeleteRule:
        async def test_deletes_rule(
            self, manager: FirewallRuleManager, sample_rule: FirewallRule
        ) -> None:
            await manager.create_rule(sample_rule)
            await manager.delete_rule("r1")
            with pytest.raises(RuleNotFoundError):
                await manager.get_rule("r1")

    class TestListRules:
        async def test_empty_when_none(self, manager: FirewallRuleManager) -> None:
            assert await manager.list_rules() == []

        async def test_filters_by_environment(
            self, manager: FirewallRuleManager, sample_rule: FirewallRule
        ) -> None:
            r2 = FirewallRule(
                id="r2", name="allow-dns", action=RuleAction.ALLOW, environment="staging"
            )
            await manager.create_rule(sample_rule)
            await manager.create_rule(r2)
            result = await manager.list_rules(environment="production")
            assert len(result) == 1

        async def test_filters_by_action(
            self, manager: FirewallRuleManager, sample_rule: FirewallRule
        ) -> None:
            await manager.create_rule(sample_rule)
            result = await manager.list_rules(action=RuleAction.DENY)
            assert len(result) == 0

    class TestRuleSet:
        async def test_creates_ruleset(self, manager: FirewallRuleManager) -> None:
            rs = RuleSet(id="rs1", name="prod-rules")
            result = await manager.create_ruleset(rs)
            assert result.id == "rs1"

        async def test_activates_ruleset(self, manager: FirewallRuleManager) -> None:
            rs = RuleSet(id="rs1", name="prod-rules")
            await manager.create_ruleset(rs)
            activated = await manager.activate_ruleset("rs1")
            assert activated.status is RuleSetStatus.ACTIVE

        async def test_lists_rulesets(self, manager: FirewallRuleManager) -> None:
            rs = RuleSet(id="rs1", name="prod-rules")
            await manager.create_ruleset(rs)
            result = await manager.list_rulesets()
            assert len(result) == 1

        async def test_filters_rulesets_by_status(self, manager: FirewallRuleManager) -> None:
            rs = RuleSet(id="rs1", name="prod-rules")
            await manager.create_ruleset(rs)
            result = await manager.list_rulesets(status=RuleSetStatus.DRAFT)
            assert len(result) == 1

    class TestGetStatistics:
        async def test_returns_stats(
            self, manager: FirewallRuleManager, sample_rule: FirewallRule
        ) -> None:
            await manager.create_rule(sample_rule)
            stats = await manager.get_statistics()
            assert stats["total_rules"] == 1
            assert stats["allow"] == 1

    class TestConfig:
        def test_default_config(self) -> None:
            m = FirewallRuleManager()
            assert m.config.default_action is RuleAction.DENY

        def test_custom_config(self) -> None:
            cfg = FirewallConfig(default_action=RuleAction.ALLOW)
            m = FirewallRuleManager(config=cfg)
            assert m.config.default_action is RuleAction.ALLOW
