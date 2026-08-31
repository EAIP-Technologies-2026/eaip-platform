"""Tests for cache Pydantic models."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from eaip.cache.models import CacheConfig, CacheEntry, CacheStats


class TestCacheEntry:
    def test_default_values(self) -> None:
        entry = CacheEntry(key="k1", value=b"data")
        assert entry.key == "k1"
        assert entry.value == b"data"
        assert entry.ttl_seconds is None
        assert entry.hits == 0
        assert entry.size_bytes == 0
        assert isinstance(entry.created_at, datetime)

    def test_frozen(self) -> None:
        entry = CacheEntry(key="k", value=b"v")
        with pytest.raises(ValidationError):
            entry.key = "new"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CacheEntry(key="k", value=b"v", unknown_field="x")  # type: ignore[call-arg]

    def test_with_expiry(self) -> None:
        expires = datetime.now() + timedelta(seconds=60)
        entry = CacheEntry(key="k", value=b"v", ttl_seconds=60, expires_at=expires)
        assert entry.ttl_seconds == 60
        assert entry.expires_at == expires


class TestCacheConfig:
    def test_default_values(self) -> None:
        cfg = CacheConfig(max_size_bytes=1048576)
        assert cfg.default_ttl_seconds == 300
        assert cfg.max_size_bytes == 1048576
        assert cfg.max_entries == 10000
        assert cfg.namespace == "default"
        assert cfg.enable_stats is False

    def test_frozen(self) -> None:
        cfg = CacheConfig(max_size_bytes=100)
        with pytest.raises(ValidationError):
            cfg.namespace = "other"  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CacheConfig(max_size_bytes=100, unknown=True)  # type: ignore[call-arg]

    def test_custom_values(self) -> None:
        cfg = CacheConfig(
            default_ttl_seconds=60,
            max_size_bytes=5000,
            max_entries=500,
            namespace="custom",
            enable_stats=True,
        )
        assert cfg.default_ttl_seconds == 60
        assert cfg.enable_stats is True


class TestCacheStats:
    def test_default_values(self) -> None:
        stats = CacheStats()
        assert stats.total_entries == 0
        assert stats.total_hits == 0
        assert stats.total_misses == 0
        assert stats.total_evictions == 0
        assert stats.hit_ratio == 0.0
        assert stats.size_bytes == 0

    def test_frozen(self) -> None:
        stats = CacheStats(total_entries=10)
        with pytest.raises(ValidationError):
            stats.total_entries = 20  # type: ignore[misc]

    def test_extra_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CacheStats(unknown=True)  # type: ignore[call-arg]

    def test_custom_values(self) -> None:
        stats = CacheStats(
            total_entries=100,
            total_hits=80,
            total_misses=20,
            total_evictions=5,
            hit_ratio=0.8,
            size_bytes=4096,
        )
        assert stats.hit_ratio == 0.8
        assert stats.total_entries == 100
