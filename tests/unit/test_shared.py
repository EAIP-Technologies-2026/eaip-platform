"""Tests for :mod:`eaip.shared`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from eaip.shared.identifiers import ComponentId, CorrelationId, RunId, Slug
from eaip.shared.result import Err, Ok
from eaip.shared.sentinels import UNSET, UnsetType
from eaip.shared.time import Duration, utc_now


class TestIdentifiers:
    def test_new_produces_distinct_ids(self) -> None:
        a, b = CorrelationId.new(), CorrelationId.new()
        assert a != b
        assert isinstance(a, str)
        assert isinstance(a, CorrelationId)

    def test_parse_rejects_empty(self) -> None:
        with pytest.raises(ValueError):
            CorrelationId.parse("")

    def test_types_are_statically_distinct(self) -> None:
        cid = CorrelationId.new()
        rid = RunId(cid)
        # Same string value, different Python types — that's the point.
        assert isinstance(cid, CorrelationId) and not isinstance(cid, RunId)
        assert isinstance(rid, RunId)

    def test_component_id_factory(self) -> None:
        cid = ComponentId.new()
        assert ComponentId.parse(cid) == cid

    @pytest.mark.parametrize("ok", ["x", "a-b-c", "abc123", "z" + "y" * 62])
    def test_slug_accepts(self, ok: str) -> None:
        Slug(ok)

    @pytest.mark.parametrize("bad", ["", "-x", "x-", "X", "a_b", "a" * 65])
    def test_slug_rejects(self, bad: str) -> None:
        with pytest.raises(ValueError):
            Slug(bad)


class TestResult:
    def test_ok_unwrap(self) -> None:
        r: Ok[int] = Ok(7)
        assert r.is_ok and not r.is_err
        assert r.unwrap() == 7
        assert r.map(lambda v: v * 2).unwrap() == 14

    def test_err_unwrap_raises(self) -> None:
        e: Err[str] = Err("boom")
        assert e.is_err and not e.is_ok
        with pytest.raises(RuntimeError):
            e.unwrap()
        assert e.unwrap_or(99) == 99


class TestSentinels:
    def test_unset_is_singleton_and_falsy(self) -> None:
        assert UNSET is UnsetType.UNSET
        assert not UNSET
        assert repr(UNSET) == "UNSET"


class TestTime:
    def test_utc_now_is_aware(self) -> None:
        n = utc_now()
        assert n.tzinfo is timezone.utc

    def test_duration_construction(self) -> None:
        d = Duration.from_milliseconds(1500)
        assert d.microseconds == 1_500_000
        assert d.seconds == pytest.approx(1.5)
        assert d.to_timedelta() == timedelta(milliseconds=1500)

    def test_duration_rejects_negative(self) -> None:
        with pytest.raises(ValueError):
            Duration(-1)

    def test_duration_orders(self) -> None:
        assert Duration(1) < Duration(2)
