"""Tests for :mod:`eaip.modelreg.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.modelreg.models import (
    ModelArtifact,
    ModelRegistryConfig,
    ModelRegistryEntry,
    ModelVersion,
)


class TestModelVersion:
    """Tests for :class:`eaip.modelreg.models.ModelVersion`."""

    def test_create_minimal(self) -> None:
        """Test creating a version with required fields."""
        v = ModelVersion(version="1.0.0")
        assert v.version == "1.0.0"
        assert v.description == ""

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        v = ModelVersion(version="1.0.0")
        with pytest.raises(ValidationError):
            v.version = "2.0.0"


class TestModelArtifact:
    """Tests for :class:`eaip.modelreg.models.ModelArtifact`."""

    def test_create_minimal(self) -> None:
        """Test creating an artifact with required fields."""
        a = ModelArtifact(uri="s3://bucket/model", type="onnx")
        assert a.uri == "s3://bucket/model"
        assert a.size_bytes == 0

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        a = ModelArtifact(uri="u", type="t")
        with pytest.raises(ValidationError):
            a.uri = "changed"


class TestModelRegistryEntry:
    """Tests for :class:`eaip.modelreg.models.ModelRegistryEntry`."""

    def test_create_minimal(self) -> None:
        """Test creating an entry with required fields."""
        e = ModelRegistryEntry(id="m1", name="GPT-4", provider="openai")
        assert e.is_deprecated is False

    def test_with_versions(self) -> None:
        """Test creating an entry with versions."""
        v = ModelVersion(version="1.0.0")
        e = ModelRegistryEntry(
            id="m1",
            name="GPT-4",
            provider="openai",
            versions=(v,),
        )
        assert len(e.versions) == 1

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        e = ModelRegistryEntry(id="m1", name="Test", provider="p")
        with pytest.raises(ValidationError):
            e.name = "Changed"


class TestModelRegistryConfig:
    """Tests for :class:`eaip.modelreg.models.ModelRegistryConfig`."""

    def test_defaults(self) -> None:
        """Test default configuration values."""
        c = ModelRegistryConfig()
        assert c.max_versions_per_model == 10
        assert c.allow_downgrade is False

    def test_custom(self) -> None:
        """Test creating a config with custom values."""
        c = ModelRegistryConfig(max_versions_per_model=5, allow_downgrade=True)
        assert c.max_versions_per_model == 5
        assert c.allow_downgrade is True

    def test_frozen(self) -> None:
        """Test that instances are immutable."""
        c = ModelRegistryConfig()
        with pytest.raises(ValidationError):
            c.max_versions_per_model = 20


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are rejected."""
    with pytest.raises(ValidationError):
        ModelRegistryEntry(id="m1", name="Test", provider="p", unknown="val")
