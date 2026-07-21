"""Tests for StatusPageService."""

from __future__ import annotations

import pytest

from eaip.health.checks import HealthStatus
from eaip.healthagg.exceptions import StatusPageNotFoundError
from eaip.healthagg.models import StatusPageStatus
from eaip.healthagg.status_page import StatusPageService


class _MockAggregator:
    async def get_all_components(self) -> dict[str, HealthStatus]:
        return {
            "api": HealthStatus.HEALTHY,
            "db": HealthStatus.DEGRADED,
            "cache": HealthStatus.UNHEALTHY,
        }


class TestStatusPageService:
    def test_create_page_minimal(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(name="Main Status")
        assert page.id is not None
        assert page.name == "Main Status"
        assert page.components == ()
        assert page.public is False
        assert page.status == StatusPageStatus.ACTIVE

    def test_create_page_full(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(
            name="Full Page",
            description="Desc",
            components=("api", "db"),
            layout={"columns": 2},
            refresh_interval_seconds=120,
            public=True,
            metadata={"owner": "team-a"},
        )
        assert page.components == ("api", "db")
        assert page.layout == {"columns": 2}
        assert page.refresh_interval_seconds == 120
        assert page.public is True

    def test_get_page(self) -> None:
        svc = StatusPageService()
        created = svc.create_page(name="Test")
        retrieved = svc.get_page(created.id)
        assert retrieved.id == created.id
        assert retrieved.name == "Test"

    def test_get_page_not_found(self) -> None:
        svc = StatusPageService()
        with pytest.raises(StatusPageNotFoundError):
            svc.get_page("nonexistent")

    def test_update_page(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(name="Old Name")
        updated = svc.update_page(page.id, name="New Name")
        assert updated.name == "New Name"
        assert updated.id == page.id

    def test_update_page_not_found(self) -> None:
        svc = StatusPageService()
        with pytest.raises(StatusPageNotFoundError):
            svc.update_page("nonexistent", name="Nope")

    def test_delete_page(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(name="Test")
        assert svc.delete_page(page.id) is True
        assert svc.delete_page("nonexistent") is False

    def test_list_pages(self) -> None:
        svc = StatusPageService()
        p1 = svc.create_page(name="Page 1")
        p2 = svc.create_page(name="Page 2")
        pages = svc.list_pages()
        assert len(pages) == 2
        assert {p.id for p in pages} == {p1.id, p2.id}

    async def test_render_page_without_aggregator(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(name="Test")
        rendered = await svc.render_page(page.id)
        assert rendered["page"]["id"] == page.id
        assert rendered["component_statuses"] == {}
        assert rendered["overall_status"] == "healthy"

    async def test_render_page_with_aggregator(self) -> None:
        agg = _MockAggregator()
        svc = StatusPageService(aggregator=agg)
        page = svc.create_page(name="Test", components=("api", "db", "cache"))
        rendered = await svc.render_page(page.id)
        assert rendered["component_statuses"]["api"] == "healthy"
        assert rendered["component_statuses"]["db"] == "degraded"
        assert rendered["component_statuses"]["cache"] == "unhealthy"
        assert rendered["overall_status"] == "unhealthy"

    async def test_get_page_status(self) -> None:
        agg = _MockAggregator()
        svc = StatusPageService(aggregator=agg)
        page = svc.create_page(name="Test", components=("api", "db"))
        status = await svc.get_page_status(page.id)
        assert status == HealthStatus.DEGRADED

    async def test_get_page_status_no_aggregator(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(name="Test")
        status = await svc.get_page_status(page.id)
        assert status == HealthStatus.HEALTHY

    async def test_publish_page(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(name="My Service Status", public=False)
        url = await svc.publish_page(page.id)
        assert url == "/status/my-service-status"
        updated = svc.get_page(page.id)
        assert updated.public is True

    def test_set_public_access_enable(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(name="Test", public=False)
        updated = svc.set_public_access(page.id, True)
        assert updated.public is True

    def test_set_public_access_disable(self) -> None:
        svc = StatusPageService()
        page = svc.create_page(name="Test", public=True)
        updated = svc.set_public_access(page.id, False)
        assert updated.public is False
