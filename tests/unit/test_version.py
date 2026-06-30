"""Tests for :mod:`eaip.version`."""

from __future__ import annotations

import pytest

from eaip.version import PLATFORM_VERSION, Version


def test_platform_version_is_semver() -> None:
    parsed = Version.parse(PLATFORM_VERSION)
    assert parsed.major >= 0


def test_parse_roundtrip() -> None:
    assert str(Version.parse("1.2.3-rc.1+build.5")) == "1.2.3-rc.1+build.5"


def test_invalid_raises() -> None:
    with pytest.raises(ValueError):
        Version.parse("v1.0")


def test_ordering() -> None:
    a = Version.parse("1.2.3")
    b = Version.parse("1.2.4")
    c = Version.parse("1.2.3-alpha")
    assert a < b
    assert c < a  # pre-release < release


def test_compatibility() -> None:
    assert Version.parse("1.4.0").is_compatible_with(Version.parse("1.0.0"))
    assert not Version.parse("2.0.0").is_compatible_with(Version.parse("1.0.0"))
    # Pre-1.0: stricter — major+minor must match.
    assert Version.parse("0.1.0").is_compatible_with(Version.parse("0.1.5"))
    assert not Version.parse("0.1.0").is_compatible_with(Version.parse("0.2.0"))
