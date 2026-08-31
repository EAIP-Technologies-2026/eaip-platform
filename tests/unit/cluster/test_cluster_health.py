"""Tests for ClusterHealthCheck."""

from __future__ import annotations

from eaip.cluster.health import ClusterHealthCheck
from eaip.health.checks import HealthCheck, HealthStatus


class TestClusterHealthCheck:
    async def test_healthy_no_nodes(self) -> None:
        check = ClusterHealthCheck(node_count=0)
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.details["node_count"] == 0
        assert report.details["leader"] is None

    async def test_healthy_with_leader(self) -> None:
        check = ClusterHealthCheck(node_count=3, leader_id="node_1")
        report = await check.check()
        assert report.status is HealthStatus.HEALTHY
        assert report.details["node_count"] == 3
        assert report.details["leader"] == "node_1"

    async def test_degraded_no_leader(self) -> None:
        check = ClusterHealthCheck(node_count=3, leader_id=None)
        report = await check.check()
        assert report.status is HealthStatus.DEGRADED
        assert "no leader elected" in report.message

    async def test_name_property(self) -> None:
        check = ClusterHealthCheck()
        assert check.name == "eaip.cluster"

    async def test_implements_protocol(self) -> None:
        check = ClusterHealthCheck()
        assert isinstance(check, HealthCheck)
