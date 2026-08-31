"""Tests for :mod:`eaip.helmrepo.events`."""

from __future__ import annotations

import pytest

from eaip.helmrepo.events import (
    ChartDeprecated,
    ChartUploaded,
    ReleaseDeployed,
    ReleaseRolledBack,
)


class TestChartUploaded:
    def test_create(self) -> None:
        e = ChartUploaded(chart_id="c1", name="my-chart", version="1.0.0")
        assert e.event_type == "eaip.helmrepo.chart.uploaded"

    def test_frozen(self) -> None:
        e = ChartUploaded(chart_id="c1", name="n", version="v1")
        with pytest.raises(ValueError):
            e.chart_id = "c2"


class TestChartDeprecated:
    def test_create(self) -> None:
        e = ChartDeprecated(chart_id="c1", name="old-chart", reason="replaced")
        assert e.event_type == "eaip.helmrepo.chart.deprecated"


class TestReleaseDeployed:
    def test_create(self) -> None:
        e = ReleaseDeployed(release_id="r1", chart_id="c1", environment="prod", revision=2)
        assert e.event_type == "eaip.helmrepo.release.deployed"


class TestReleaseRolledBack:
    def test_create(self) -> None:
        e = ReleaseRolledBack(
            release_id="r1", chart_id="c1", environment="prod", previous_revision=2, new_revision=1
        )
        assert e.event_type == "eaip.helmrepo.release.rolled_back"


def test_all_events_have_unique_types() -> None:
    types = [
        ChartUploaded(chart_id="c", name="n", version="v").event_type,
        ChartDeprecated(chart_id="c", name="n", reason="r").event_type,
        ReleaseDeployed(release_id="r", chart_id="c", environment="e", revision=1).event_type,
        ReleaseRolledBack(
            release_id="r", chart_id="c", environment="e", previous_revision=1, new_revision=2
        ).event_type,
    ]
    assert len(types) == len(set(types))
