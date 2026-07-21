"""Helm chart repository service — chart storage, release management."""

from __future__ import annotations

from eaip.helmrepo.exceptions import ChartNotFoundError
from eaip.helmrepo.models import ChartRelease, HelmChart, HelmChartStatus, HelmConfig


class HelmChartRepository:
    def __init__(self, config: HelmConfig | None = None) -> None:
        self._config = config or HelmConfig()
        self._charts: dict[str, HelmChart] = {}
        self._releases: dict[str, ChartRelease] = {}

    @property
    def config(self) -> HelmConfig:
        return self._config

    async def store_chart(self, chart: HelmChart) -> HelmChart:
        self._charts[chart.id] = chart
        return chart

    async def get_chart(self, chart_id: str) -> HelmChart:
        chart = self._charts.get(chart_id)
        if chart is None:
            raise ChartNotFoundError(f"Chart {chart_id} not found")
        return chart

    async def deprecate_chart(self, chart_id: str) -> HelmChart:
        chart = await self.get_chart(chart_id)
        updated = chart.model_copy(update={"status": HelmChartStatus.DEPRECATED})
        self._charts[chart_id] = updated
        return updated

    async def create_release(self, release: ChartRelease) -> ChartRelease:
        self._releases[release.id] = release
        return release

    async def list_charts(self) -> list[HelmChart]:
        return list(self._charts.values())

    async def list_releases(self) -> list[ChartRelease]:
        return list(self._releases.values())


__all__ = ["HelmChartRepository"]
