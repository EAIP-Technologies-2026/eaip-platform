"""Tests for :mod:`eaip.maskpolicy.models`."""

from __future__ import annotations

import pytest

from eaip.maskpolicy.models import MaskingConfig, MaskingPolicy, MaskingRule, PolicyStatus


class TestMaskingRule:
    def test_defaults(self) -> None:
        r = MaskingRule(id="r1", name="Email Mask")
        assert r.pattern == ""
        assert r.mask_char == "*"
        assert r.preserve_length is True
        assert r.preserve_prefix == 0
        assert r.apply_to_fields == ()
        assert r.enabled is True

    def test_with_all_fields(self) -> None:
        r = MaskingRule(
            id="r2",
            name="SSN Mask",
            pattern=r"\d{3}-\d{2}-\d{4}",
            mask_char="#",
            preserve_length=False,
            preserve_prefix=4,
            apply_to_fields=("ssn",),
            enabled=False,
        )
        assert r.mask_char == "#"
        assert r.preserve_length is False
        assert r.preserve_prefix == 4
        assert "ssn" in r.apply_to_fields
        assert r.enabled is False

    def test_frozen(self) -> None:
        r = MaskingRule(id="r1", name="N")
        with pytest.raises((ValueError, TypeError)):
            r.name = "new"  # type: ignore[misc]


class TestMaskingPolicy:
    def test_defaults(self) -> None:
        p = MaskingPolicy(id="p1", name="PCI Policy")
        assert p.rules == ()
        assert p.data_types == ()
        assert p.environment == "production"
        assert p.status is PolicyStatus.DRAFT

    def test_with_rules(self) -> None:
        r = MaskingRule(id="r1", name="CC Mask")
        p = MaskingPolicy(
            id="p2",
            name="Prod Policy",
            rules=(r,),
            data_types=("creditcard", "ssn"),
            environment="prod",
            status=PolicyStatus.ACTIVE,
        )
        assert len(p.rules) == 1
        assert len(p.data_types) == 2

    def test_frozen(self) -> None:
        p = MaskingPolicy(id="p1", name="N")
        with pytest.raises((ValueError, TypeError)):
            p.name = "new"  # type: ignore[misc]

    def test_status_values(self) -> None:
        assert PolicyStatus.ACTIVE.value == "active"
        assert PolicyStatus.DRAFT.value == "draft"
        assert PolicyStatus.ARCHIVED.value == "archived"


class TestMaskingConfig:
    def test_defaults(self) -> None:
        c = MaskingConfig()
        assert c.default_mask_char == "*"
        assert c.enable_audit_logging is True
        assert c.max_policies == 50

    def test_custom_values(self) -> None:
        c = MaskingConfig(
            default_mask_char="#",
            enable_audit_logging=False,
            max_policies=100,
        )
        assert c.default_mask_char == "#"
        assert c.enable_audit_logging is False
        assert c.max_policies == 100

    def test_frozen(self) -> None:
        c = MaskingConfig()
        with pytest.raises((ValueError, TypeError)):
            c.max_policies = 10  # type: ignore[misc]
