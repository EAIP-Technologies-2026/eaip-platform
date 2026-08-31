"""Tests for :mod:`eaip.datamask.masking`."""

from __future__ import annotations

import hashlib

import pytest

from eaip.datamask.masking import DataMaskingService
from eaip.datamask.models import DataType, MaskingRule, MaskingStrategy


class TestDataMaskingService:
    @pytest.fixture
    def service(self) -> DataMaskingService:
        return DataMaskingService()

    @pytest.fixture
    def email_rule(self) -> MaskingRule:
        return MaskingRule(
            id="r1",
            name="Email Mask",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )

    @pytest.fixture
    def ssn_rule(self) -> MaskingRule:
        return MaskingRule(
            id="r2",
            name="SSN Redact",
            field_pattern="ssn",
            data_type=DataType.SSN,
            strategy=MaskingStrategy.REDACT,
        )

    async def test_create_and_get_rule(self, service: DataMaskingService) -> None:
        rule = MaskingRule(
            id="r1",
            name="Email Mask",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        created = await service.create_rule(rule)
        assert created.id == "r1"

        fetched = await service.get_rule("r1")
        assert fetched.name == "Email Mask"

    async def test_get_rule_not_found(self, service: DataMaskingService) -> None:
        with pytest.raises(Exception):
            await service.get_rule("nonexistent")

    async def test_update_rule(self, service: DataMaskingService) -> None:
        rule = MaskingRule(
            id="r1",
            name="Original",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        await service.create_rule(rule)
        updated = await service.update_rule("r1", name="Updated", enabled=False)
        assert updated.name == "Updated"
        assert updated.enabled is False

    async def test_delete_rule(self, service: DataMaskingService) -> None:
        rule = MaskingRule(
            id="r1",
            name="Delete Me",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        await service.create_rule(rule)
        await service.delete_rule("r1")
        with pytest.raises(Exception):
            await service.get_rule("r1")

    async def test_list_rules(self, service: DataMaskingService) -> None:
        r1 = MaskingRule(
            id="r1",
            name="R1",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        r2 = MaskingRule(
            id="r2",
            name="R2",
            field_pattern="phone",
            data_type=DataType.PHONE,
            strategy=MaskingStrategy.TRUNCATE,
        )
        await service.create_rule(r1)
        await service.create_rule(r2)
        rules = await service.list_rules()
        assert len(rules) == 2

    async def test_apply_masking(self, service: DataMaskingService) -> None:
        rule = MaskingRule(
            id="r1",
            name="Email Mask",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.MASK,
        )
        data = {"email": "user@example.com", "name": "John Doe"}
        masked = await service.apply_masking(data, (rule,))
        assert "user@example.com" not in masked["email"]
        assert masked["name"] == "John Doe"

    async def test_mask_field_mask_strategy(self, service: DataMaskingService) -> None:
        config = MaskingRule(
            id="r1",
            name="Test",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.MASK,
        )
        result = await service.mask_field("hello", MaskingStrategy.MASK, config)
        assert result == "*****"
        assert len(result) == 5

    async def test_mask_field_mask_with_prefix(self, service: DataMaskingService) -> None:
        config = MaskingRule(
            id="r1",
            name="Test",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.MASK,
            preserve_prefix_count=2,
        )
        result = await service.mask_field("hello", MaskingStrategy.MASK, config)
        assert len(result) == 5
        assert result[:2] == "he"
        assert result[2:] == "***"

    async def test_mask_field_truncate(self, service: DataMaskingService) -> None:
        config = MaskingRule(
            id="r1",
            name="Test",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.TRUNCATE,
            preserve_prefix_count=3,
        )
        result = await service.mask_field("hello123", MaskingStrategy.TRUNCATE, config)
        assert result == "hel"

    async def test_mask_field_hash(self, service: DataMaskingService) -> None:
        config = MaskingRule(
            id="r1",
            name="Test",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.HASH,
        )
        result = await service.mask_field("secret", MaskingStrategy.HASH, config)
        expected = hashlib.sha256(b"secret").hexdigest()
        assert result == expected

    async def test_mask_field_redact(self, service: DataMaskingService) -> None:
        config = MaskingRule(
            id="r1",
            name="Test",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.REDACT,
        )
        result = await service.mask_field("sensitive!!!", MaskingStrategy.REDACT, config)
        assert "[REDACTED" in result
        assert "12 chars" in result

    async def test_mask_field_substitute(self, service: DataMaskingService) -> None:
        config = MaskingRule(
            id="r1",
            name="Test",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.SUBSTITUTE,
            substitution_dict={"secret": "***"},
        )
        result = await service.mask_field("secret", MaskingStrategy.SUBSTITUTE, config)
        assert result == "***"

    async def test_mask_field_substitute_not_found(self, service: DataMaskingService) -> None:
        config = MaskingRule(
            id="r1",
            name="Test",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.SUBSTITUTE,
            substitution_dict={"secret": "***"},
        )
        result = await service.mask_field("unknown", MaskingStrategy.SUBSTITUTE, config)
        assert result == "unknown"

    async def test_mask_field_non_string(self, service: DataMaskingService) -> None:
        config = MaskingRule(
            id="r1",
            name="Test",
            field_pattern="f",
            data_type=DataType.CUSTOM,
            strategy=MaskingStrategy.MASK,
        )
        result = await service.mask_field(12345, MaskingStrategy.MASK, config)
        assert result == 12345

    async def test_disabled_rule_skipped(self, service: DataMaskingService) -> None:
        rule = MaskingRule(
            id="r1",
            name="Disabled",
            field_pattern="email",
            data_type=DataType.EMAIL,
            strategy=MaskingStrategy.REDACT,
            enabled=False,
        )
        data = {"email": "user@example.com"}
        masked = await service.apply_masking(data, (rule,))
        assert masked["email"] == "user@example.com"
