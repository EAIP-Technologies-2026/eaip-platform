"""Tests for :mod:`eaip.contentmod.moderator`."""

from __future__ import annotations

import pytest

from eaip.contentmod.exceptions import ModerationError, RuleNotFoundError
from eaip.contentmod.models import (
    ContentItem,
    ContentModerationConfig,
    ContentStatus,
    ModerationAction,
    ModerationRule,
)
from eaip.contentmod.moderator import ContentModerator


class TestContentModerator:
    @pytest.fixture
    def moderator(self) -> ContentModerator:
        return ContentModerator()

    @pytest.fixture
    def sample_rule(self) -> ModerationRule:
        return ModerationRule(
            id="r1",
            name="Block bad words",
            pattern=r"badword",
            action=ModerationAction.BLOCK,
            priority=10,
        )

    @pytest.fixture
    def sample_item(self) -> ContentItem:
        return ContentItem(
            id="c1",
            source="web",
            content_type="text",
            text_content="clean content",
            submitted_by="user1",
        )

    class TestRegisterRule:
        async def test_register(
            self, moderator: ContentModerator, sample_rule: ModerationRule
        ) -> None:
            result = await moderator.register_rule(sample_rule)
            assert result.id == "r1"

        async def test_list_rules(
            self, moderator: ContentModerator, sample_rule: ModerationRule
        ) -> None:
            await moderator.register_rule(sample_rule)
            rules = await moderator.list_rules()
            assert len(rules) == 1

    class TestModerate:
        async def test_clean_content_auto_review(
            self, moderator: ContentModerator, sample_item: ContentItem
        ) -> None:
            result = await moderator.moderate(sample_item)
            assert result.action == ModerationAction.REVIEW

        async def test_blocked_content(
            self, moderator: ContentModerator, sample_rule: ModerationRule
        ) -> None:
            await moderator.register_rule(sample_rule)
            item = ContentItem(
                id="c2",
                source="web",
                content_type="text",
                text_content="contains badword here",
                submitted_by="user2",
            )
            result = await moderator.moderate(item)
            assert result.action == ModerationAction.BLOCK

        async def test_flagged_content(self, moderator: ContentModerator) -> None:
            rule = ModerationRule(
                id="r2",
                name="Flag suspicious",
                pattern=r"suspicious",
                action=ModerationAction.FLAG,
                priority=5,
            )
            await moderator.register_rule(rule)
            item = ContentItem(
                id="c3",
                source="web",
                content_type="text",
                text_content="this is suspicious",
                submitted_by="user3",
            )
            result = await moderator.moderate(item)
            assert result.action == ModerationAction.FLAG

        async def test_auto_approve(self) -> None:
            config = ContentModerationConfig(auto_approve=True)
            mod = ContentModerator(config=config)
            item = ContentItem(
                id="c4",
                source="web",
                content_type="text",
                text_content="clean",
                submitted_by="user4",
            )
            result = await mod.moderate(item)
            assert result.action == ModerationAction.REVIEW

    class TestApprove:
        async def test_approve(self, moderator: ContentModerator, sample_item: ContentItem) -> None:
            await moderator.moderate(sample_item)
            result = await moderator.approve("c1", "mod1")
            assert result.status == ContentStatus.APPROVED

    class TestReject:
        async def test_reject(self, moderator: ContentModerator, sample_item: ContentItem) -> None:
            await moderator.moderate(sample_item)
            result = await moderator.reject("c1", "inappropriate content", "mod1")
            assert result.status == ContentStatus.REJECTED

    class TestGetItem:
        async def test_get_item(
            self, moderator: ContentModerator, sample_item: ContentItem
        ) -> None:
            await moderator.moderate(sample_item)
            item = await moderator.get_item("c1")
            assert item.source == "web"

        async def test_not_found(self, moderator: ContentModerator) -> None:
            with pytest.raises(ModerationError):
                await moderator.get_item("nonexistent")

    class TestGetRule:
        async def test_get_rule(
            self, moderator: ContentModerator, sample_rule: ModerationRule
        ) -> None:
            await moderator.register_rule(sample_rule)
            rule = await moderator.get_rule("r1")
            assert rule.name == "Block bad words"

        async def test_not_found(self, moderator: ContentModerator) -> None:
            with pytest.raises(RuleNotFoundError):
                await moderator.get_rule("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            m = ContentModerator()
            assert m.config.auto_approve is False
            assert m.config.enable_blocking is True

        def test_custom_config(self) -> None:
            config = ContentModerationConfig(auto_approve=True, enable_blocking=False)
            m = ContentModerator(config=config)
            assert m.config.auto_approve is True
            assert m.config.enable_blocking is False
