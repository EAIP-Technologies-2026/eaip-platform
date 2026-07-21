"""ContentModerator — central service for content moderation."""

from __future__ import annotations

import re

from eaip.contentmod.events import ContentApproved, ContentRejected
from eaip.contentmod.exceptions import ModerationError, RuleNotFoundError
from eaip.contentmod.models import (
    ContentItem,
    ContentModerationConfig,
    ContentStatus,
    ModerationAction,
    ModerationResult,
    ModerationRule,
)
from eaip.logging.context import get_logger


class ContentModerator:
    def __init__(self, config: ContentModerationConfig | None = None) -> None:
        self._config = config or ContentModerationConfig()
        self._items: dict[str, ContentItem] = {}
        self._rules: dict[str, ModerationRule] = {}
        self._results: dict[str, ModerationResult] = {}
        self._log = get_logger("eaip.contentmod.moderator")

    @property
    def config(self) -> ContentModerationConfig:
        return self._config

    async def register_rule(self, rule: ModerationRule) -> ModerationRule:
        self._rules[rule.id] = rule
        self._log.info("contentmod.rule.registered", rule_id=rule.id, name=rule.name)
        return rule

    async def moderate(self, item: ContentItem) -> ModerationResult:
        self._items[item.id] = item
        sorted_rules = sorted(self._rules.values(), key=lambda r: r.priority, reverse=True)
        for rule in sorted_rules:
            if re.search(rule.pattern, item.text_content):
                result = await self._apply_rule(item, rule)
                return result
        if self._config.auto_approve:
            return await self._approve(item)
        result_id = f"result_{item.id}"
        result = ModerationResult(
            id=result_id,
            content_id=item.id,
            rule_id="",
            action=ModerationAction.REVIEW,
            reason="No matching rules; default review",
        )
        self._results[result_id] = result
        return result

    async def _apply_rule(self, item: ContentItem, rule: ModerationRule) -> ModerationResult:
        result_id = f"result_{item.id}"
        action = rule.action
        updated_status = ContentStatus.APPROVED
        reason = f"Matched rule '{rule.name}'"
        if action == ModerationAction.BLOCK:
            updated_status = ContentStatus.REJECTED
            reason = f"Blocked by rule '{rule.name}'"
        elif action == ModerationAction.FLAG:
            updated_status = ContentStatus.FLAGGED
            reason = f"Flagged by rule '{rule.name}'"
        elif action == ModerationAction.REVIEW:
            updated_status = ContentStatus.FLAGGED
            reason = f"Flagged for review by rule '{rule.name}'"
        updated = ContentItem(
            id=item.id,
            source=item.source,
            content_type=item.content_type,
            text_content=item.text_content,
            status=updated_status,
            submitted_by=item.submitted_by,
            submitted_at=item.submitted_at,
        )
        self._items[item.id] = updated
        result = ModerationResult(
            id=result_id,
            content_id=item.id,
            rule_id=rule.id,
            action=action,
            reason=reason,
        )
        self._results[result_id] = result
        if action == ModerationAction.FLAG or action == ModerationAction.BLOCK:
            pass
        self._log.info("contentmod.rule.applied", item_id=item.id, rule_id=rule.id, action=action)
        return result

    async def _approve(self, item: ContentItem) -> ModerationResult:
        updated = ContentItem(
            id=item.id,
            source=item.source,
            content_type=item.content_type,
            text_content=item.text_content,
            status=ContentStatus.APPROVED,
            submitted_by=item.submitted_by,
            submitted_at=item.submitted_at,
        )
        self._items[item.id] = updated
        result_id = f"result_{item.id}"
        result = ModerationResult(
            id=result_id,
            content_id=item.id,
            rule_id="",
            action=ModerationAction.REVIEW,
            reason="Auto-approved",
        )
        self._results[result_id] = result
        return result

    async def approve(self, content_id: str, moderated_by: str) -> ContentItem:
        item = self._get_item(content_id)
        updated = ContentItem(
            id=item.id,
            source=item.source,
            content_type=item.content_type,
            text_content=item.text_content,
            status=ContentStatus.APPROVED,
            submitted_by=item.submitted_by,
            submitted_at=item.submitted_at,
        )
        self._items[content_id] = updated
        event = ContentApproved(content_id=content_id, moderated_by=moderated_by)
        self._log.info("contentmod.content.approved", content_id=content_id)
        return updated

    async def reject(self, content_id: str, reason: str, moderated_by: str) -> ContentItem:
        item = self._get_item(content_id)
        updated = ContentItem(
            id=item.id,
            source=item.source,
            content_type=item.content_type,
            text_content=item.text_content,
            status=ContentStatus.REJECTED,
            submitted_by=item.submitted_by,
            submitted_at=item.submitted_at,
        )
        self._items[content_id] = updated
        event = ContentRejected(content_id=content_id, reason=reason, moderated_by=moderated_by)
        self._log.info("contentmod.content.rejected", content_id=content_id)
        return updated

    async def get_item(self, content_id: str) -> ContentItem:
        return self._get_item(content_id)

    async def list_items(self) -> list[ContentItem]:
        return list(self._items.values())

    async def get_rule(self, rule_id: str) -> ModerationRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise RuleNotFoundError(f"Rule '{rule_id}' not found")
        return rule

    async def list_rules(self) -> list[ModerationRule]:
        return list(self._rules.values())

    def _get_item(self, content_id: str) -> ContentItem:
        item = self._items.get(content_id)
        if item is None:
            raise ModerationError(f"Content item '{content_id}' not found")
        return item
