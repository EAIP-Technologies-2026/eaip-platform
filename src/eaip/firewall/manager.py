"""FirewallRuleManager — create, update, delete, and organize firewall rules."""

from __future__ import annotations

from eaip.events.bus import EventBus
from eaip.firewall.events import RuleCreated, RuleDeleted, RuleSetActivated, RuleUpdated
from eaip.firewall.exceptions import RuleNotFoundError
from eaip.firewall.models import (
    FirewallConfig,
    FirewallRule,
    RuleAction,
    RuleSet,
    RuleSetStatus,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class FirewallRuleManager:
    """Central service for managing firewall rules and rule sets."""

    def __init__(self, config: FirewallConfig | None = None, event_bus: EventBus | None = None) -> None:
        self._config = config or FirewallConfig()
        self._rules: dict[str, FirewallRule] = {}
        self._rulesets: dict[str, RuleSet] = {}
        self._log = get_logger("eaip.firewall.manager")
        self._event_bus = event_bus

    @property
    def config(self) -> FirewallConfig:
        return self._config

    async def create_rule(self, rule: FirewallRule) -> FirewallRule:
        """Create a new firewall rule."""
        self._rules[rule.id] = rule
        if self._event_bus is not None:
            await self._event_bus.publish(
                RuleCreated(
                    rule_id=rule.id,
                    name=rule.name,
                    action=rule.action.value,
                    environment=rule.environment,
                )
            )
        self._log.info(
            "firewall.rule.created",
            rule_id=rule.id,
            name=rule.name,
        )
        return rule

    async def get_rule(self, rule_id: str) -> FirewallRule:
        """Get a firewall rule by ID."""
        rule = self._rules.get(rule_id)
        if rule is None:
            raise RuleNotFoundError(f"Firewall rule not found: {rule_id}")
        return rule

    async def update_rule(self, rule_id: str, **updates: object) -> FirewallRule:
        """Update a firewall rule."""
        existing = await self.get_rule(rule_id)
        updated = existing.model_copy(update=updates)
        self._rules[rule_id] = updated
        if self._event_bus is not None:
            await self._event_bus.publish(
                RuleUpdated(
                    rule_id=rule_id,
                    changes={k: str(v) for k, v in updates.items()},
                )
            )
        self._log.info("firewall.rule.updated", rule_id=rule_id)
        return updated

    async def delete_rule(self, rule_id: str) -> None:
        """Delete a firewall rule."""
        rule = await self.get_rule(rule_id)
        del self._rules[rule_id]
        if self._event_bus is not None:
            await self._event_bus.publish(
                RuleDeleted(
                    rule_id=rule_id,
                    name=rule.name,
                )
            )
        self._log.info("firewall.rule.deleted", rule_id=rule_id)

    async def list_rules(
        self,
        environment: str | None = None,
        action: RuleAction | None = None,
        enabled: bool | None = None,
    ) -> list[FirewallRule]:
        """List firewall rules, optionally filtered."""
        result = list(self._rules.values())
        if environment is not None:
            result = [r for r in result if r.environment == environment]
        if action is not None:
            result = [r for r in result if r.action == action]
        if enabled is not None:
            result = [r for r in result if r.enabled == enabled]
        return sorted(result, key=lambda r: r.priority)

    async def create_ruleset(self, ruleset: RuleSet) -> RuleSet:
        """Create a new rule set."""
        self._rulesets[ruleset.id] = ruleset
        self._log.info("firewall.ruleset.created", ruleset_id=ruleset.id)
        return ruleset

    async def get_ruleset(self, ruleset_id: str) -> RuleSet:
        """Get a rule set by ID."""
        ruleset = self._rulesets.get(ruleset_id)
        if ruleset is None:
            raise RuleNotFoundError(f"Rule set not found: {ruleset_id}")
        return ruleset

    async def activate_ruleset(self, ruleset_id: str) -> RuleSet:
        """Activate a rule set."""
        ruleset = await self.get_ruleset(ruleset_id)
        updated = ruleset.model_copy(
            update={"status": RuleSetStatus.ACTIVE, "updated_at": utc_now()}
        )
        self._rulesets[ruleset_id] = updated
        if self._event_bus is not None:
            await self._event_bus.publish(
                RuleSetActivated(
                    ruleset_id=ruleset_id,
                    name=ruleset.name,
                    rule_count=len(ruleset.rules),
                    environment=ruleset.environment,
                )
            )
        self._log.info("firewall.ruleset.activated", ruleset_id=ruleset_id)
        return updated

    async def list_rulesets(
        self, environment: str | None = None, status: RuleSetStatus | None = None
    ) -> list[RuleSet]:
        """List rule sets, optionally filtered."""
        result = list(self._rulesets.values())
        if environment is not None:
            result = [rs for rs in result if rs.environment == environment]
        if status is not None:
            result = [rs for rs in result if rs.status == status]
        return sorted(result, key=lambda rs: rs.created_at, reverse=True)

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics about firewall rules."""
        total_rules = len(self._rules)
        enabled = sum(1 for r in self._rules.values() if r.enabled)
        disabled = total_rules - enabled
        allow = sum(1 for r in self._rules.values() if r.action is RuleAction.ALLOW)
        deny = sum(1 for r in self._rules.values() if r.action is RuleAction.DENY)
        log = sum(1 for r in self._rules.values() if r.action is RuleAction.LOG)
        return {
            "total_rules": total_rules,
            "enabled": enabled,
            "disabled": disabled,
            "allow": allow,
            "deny": deny,
            "log": log,
            "total_rulesets": len(self._rulesets),
            "active_rulesets": sum(
                1 for rs in self._rulesets.values() if rs.status is RuleSetStatus.ACTIVE
            ),
        }


__all__ = ["FirewallRuleManager"]
