from __future__ import annotations

import pytest

from eaip.observability.exceptions import SloNotFoundError
from eaip.observability.models import ObservabilityConfig, ServiceLevelObjective
from eaip.observability.slo import SliService


class TestSliService:
    def test_default_config(self) -> None:
        svc = SliService()
        assert svc.config.evaluation_interval_seconds == 60

    def test_custom_config(self) -> None:
        config = ObservabilityConfig(slo_evaluation_interval=600)
        svc = SliService(config=config)
        assert svc.config.slo_evaluation_interval == 600

    def test_create_and_get_slo(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(id="slo1", name="API Availability", target_value=99.9)
        svc.create_slo(s)
        assert svc.get_slo("slo1").name == "API Availability"

    def test_get_slo_not_found(self) -> None:
        svc = SliService()
        with pytest.raises(SloNotFoundError):
            svc.get_slo("nonexistent")

    def test_update_slo(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(id="slo1", name="Old Name", target_value=99.9)
        svc.create_slo(s)
        svc.update_slo("slo1", name="New Name", target_value=99.99)
        updated = svc.get_slo("slo1")
        assert updated.name == "New Name"
        assert updated.target_value == 99.99

    def test_delete_slo(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(id="slo1", name="To Delete", target_value=99.9)
        svc.create_slo(s)
        svc.delete_slo("slo1")
        with pytest.raises(SloNotFoundError):
            svc.get_slo("slo1")

    def test_list_slos(self) -> None:
        svc = SliService()
        s1 = ServiceLevelObjective(id="slo1", name="S1", target_value=99.9, status="active")
        s2 = ServiceLevelObjective(id="slo2", name="S2", target_value=99.0, status="paused")
        svc.create_slo(s1)
        svc.create_slo(s2)
        all_slos = svc.list_slos()
        assert len(all_slos) == 2
        active = svc.list_slos(status_filter="active")
        assert len(active) == 1
        assert active[0].id == "slo1"

    async def test_evaluate_slo_stays_active(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(id="slo1", name="API", target_value=99.9)
        svc.create_slo(s)
        updated = await svc.evaluate_slo("slo1")
        assert updated.status == "active"
        assert updated.current_value == 100.0

    async def test_evaluate_slo_paused(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(id="slo1", name="API", target_value=99.9, status="paused")
        svc.create_slo(s)
        updated = await svc.evaluate_slo("slo1")
        assert updated.status == "paused"

    async def test_evaluate_all_slos(self) -> None:
        svc = SliService()
        s1 = ServiceLevelObjective(id="slo1", name="S1", target_value=99.9)
        s2 = ServiceLevelObjective(id="slo2", name="S2", target_value=99.0)
        svc.create_slo(s1)
        svc.create_slo(s2)
        results = await svc.evaluate_all_slos()
        assert len(results) == 2

    async def test_get_slo_status(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(id="slo1", name="API", target_value=99.9)
        svc.create_slo(s)
        status = await svc.get_slo_status("slo1")
        assert status["id"] == "slo1"
        assert status["status"] == "active"
        assert status["target_percent"] == 99.9

    async def test_calculate_burn_rate(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(
            id="slo1",
            name="API",
            target_value=99.9,
            target_percent=99.9,
            current_value=99.5,
        )
        burn_rate = await svc.calculate_burn_rate(s, 300)
        assert burn_rate > 0

    async def test_calculate_burn_rate_no_error_budget(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(
            id="slo1",
            name="API",
            target_value=100.0,
            target_percent=100.0,
            current_value=100.0,
        )
        burn_rate = await svc.calculate_burn_rate(s, 300)
        assert burn_rate == 0.0

    async def test_check_burn_rate_alert(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(
            id="slo1",
            name="API",
            target_value=99.9,
            target_percent=99.9,
            current_value=50.0,
            burn_rate_threshold=2.0,
            alert_on_burn_rate=True,
        )
        assert (await svc.check_burn_rate_alert(s)) is True

    async def test_check_burn_rate_alert_disabled(self) -> None:
        svc = SliService()
        s = ServiceLevelObjective(
            id="slo1",
            name="API",
            target_value=99.9,
            alert_on_burn_rate=False,
        )
        assert (await svc.check_burn_rate_alert(s)) is False
