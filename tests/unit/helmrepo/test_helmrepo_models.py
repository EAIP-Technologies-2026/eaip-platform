"""Tests for :mod:`eaip.helmrepo.models`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from eaip.helmrepo.models import ChartRelease, HelmChart, HelmChartStatus, HelmConfig, ReleaseStatus


class TestHelmChart:
    def test_create_minimal(self) -> None:
        c = HelmChart(
            id="c1", name="my-chart", version="1.0.0", chart_data_ref="oci://registry/chart"
        )
        assert c.status is HelmChartStatus.STORED
        assert c.app_version == ""

    def test_frozen(self) -> None:
        c = HelmChart(id="c1", name="n", version="1.0.0", chart_data_ref="ref")
        with pytest.raises(ValidationError):
            c.name = "changed"


class TestChartRelease:
    def test_create(self) -> None:
        r = ChartRelease(id="r1", chart_id="c1", target_environment="production")
        assert r.revision == 1
        assert r.status is ReleaseStatus.DEPLOYED

    def test_frozen(self) -> None:
        r = ChartRelease(id="r1", chart_id="c1", target_environment="prod")
        with pytest.raises(ValidationError):
            r.revision = 2


class TestHelmConfig:
    def test_defaults(self) -> None:
        c = HelmConfig()
        assert c.max_versions_per_chart == 50
        assert c.default_timeout_seconds == 300

    def test_frozen(self) -> None:
        c = HelmConfig()
        with pytest.raises(ValidationError):
            c.storage_backend = "s3"


class TestHelmChartStatus:
    def test_values(self) -> None:
        assert HelmChartStatus.STORED.value == "stored"
        assert HelmChartStatus.ARCHIVED.value == "archived"
        assert HelmChartStatus.DEPRECATED.value == "deprecated"


class TestReleaseStatus:
    def test_values(self) -> None:
        assert ReleaseStatus.DEPLOYED.value == "deployed"
        assert ReleaseStatus.ROLLED_BACK.value == "rolled_back"


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        HelmChart(id="c1", name="n", version="1.0.0", chart_data_ref="r", unknown="x")
