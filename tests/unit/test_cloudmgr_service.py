"""Tests for CloudResourceManager service."""

from __future__ import annotations

import pytest

from eaip.cloudmgr.exceptions import ProviderNotFoundError
from eaip.cloudmgr.manager import CloudResourceManager
from eaip.cloudmgr.models import (
    CloudConfig,
    CloudProvider,
    CloudResource,
    ProviderType,
    ResourceStatus,
)


class TestCloudResourceManager:
    @pytest.fixture
    def manager(self) -> CloudResourceManager:
        return CloudResourceManager()

    @pytest.fixture
    def sample_provider(self) -> CloudProvider:
        return CloudProvider(
            id="aws1",
            name="AWS Production",
            provider_type=ProviderType.AWS,
            region="us-east-1",
        )

    @pytest.fixture
    def sample_resource(self) -> CloudResource:
        return CloudResource(
            id="res1",
            provider_id="aws1",
            resource_type="ec2",
            name="web-server-01",
            region="us-east-1",
            status=ResourceStatus.RUNNING,
            cost_per_hour=0.50,
            tags={"env": "prod"},
        )

    class TestRegisterProvider:
        async def test_register_provider(
            self, manager: CloudResourceManager, sample_provider: CloudProvider
        ) -> None:
            result = await manager.register_provider(sample_provider)
            assert result.id == "aws1"
            assert result.name == "AWS Production"

        async def test_list_providers(
            self, manager: CloudResourceManager, sample_provider: CloudProvider
        ) -> None:
            await manager.register_provider(sample_provider)
            providers = await manager.list_providers()
            assert len(providers) == 1

    class TestGetProvider:
        async def test_get_provider(
            self, manager: CloudResourceManager, sample_provider: CloudProvider
        ) -> None:
            await manager.register_provider(sample_provider)
            provider = await manager.get_provider("aws1")
            assert provider.provider_type == ProviderType.AWS

        async def test_get_provider_not_found(self, manager: CloudResourceManager) -> None:
            with pytest.raises(ProviderNotFoundError):
                await manager.get_provider("nonexistent")

    class TestAddResource:
        async def test_add_resource(
            self,
            manager: CloudResourceManager,
            sample_provider: CloudProvider,
            sample_resource: CloudResource,
        ) -> None:
            await manager.register_provider(sample_provider)
            result = await manager.add_resource(sample_resource)
            assert result.id == "res1"
            assert result.resource_type == "ec2"

        async def test_add_resource_provider_not_found(
            self, manager: CloudResourceManager, sample_resource: CloudResource
        ) -> None:
            with pytest.raises(ProviderNotFoundError):
                await manager.add_resource(sample_resource)

    class TestDiscoverResources:
        async def test_discover_resources(
            self,
            manager: CloudResourceManager,
            sample_provider: CloudProvider,
            sample_resource: CloudResource,
        ) -> None:
            await manager.register_provider(sample_provider)
            await manager.add_resource(sample_resource)
            discovered = await manager.discover_resources("aws1")
            assert len(discovered) == 1
            assert discovered[0].id == "res1"

        async def test_discover_resources_empty(
            self, manager: CloudResourceManager, sample_provider: CloudProvider
        ) -> None:
            await manager.register_provider(sample_provider)
            discovered = await manager.discover_resources("aws1")
            assert discovered == []

        async def test_discover_resources_provider_not_found(
            self, manager: CloudResourceManager
        ) -> None:
            with pytest.raises(ProviderNotFoundError):
                await manager.discover_resources("nonexistent")

    class TestCompareCosts:
        async def test_compare_costs(
            self, manager: CloudResourceManager, sample_provider: CloudProvider
        ) -> None:
            await manager.register_provider(sample_provider)
            r1 = CloudResource(id="r1", provider_id="aws1", resource_type="ec2", cost_per_hour=0.50)
            r2 = CloudResource(id="r2", provider_id="aws1", resource_type="ec2", cost_per_hour=0.75)
            await manager.add_resource(r1)
            await manager.add_resource(r2)
            estimate = await manager.compare_costs("ec2")
            assert estimate.resource_type == "ec2"
            assert estimate.estimates["aws1"] == 1.25

        async def test_compare_costs_no_resources(self, manager: CloudResourceManager) -> None:
            estimate = await manager.compare_costs("unknown")
            assert estimate.estimates == {}

    class TestListResources:
        async def test_list_all_resources(
            self,
            manager: CloudResourceManager,
            sample_provider: CloudProvider,
            sample_resource: CloudResource,
        ) -> None:
            await manager.register_provider(sample_provider)
            await manager.add_resource(sample_resource)
            resources = await manager.list_resources()
            assert len(resources) == 1

        async def test_list_by_provider(
            self, manager: CloudResourceManager, sample_provider: CloudProvider
        ) -> None:
            await manager.register_provider(sample_provider)
            p2 = CloudProvider(id="gcp1", name="GCP", provider_type=ProviderType.GCP)
            await manager.register_provider(p2)
            r1 = CloudResource(id="r1", provider_id="aws1", resource_type="vm")
            r2 = CloudResource(id="r2", provider_id="gcp1", resource_type="vm")
            await manager.add_resource(r1)
            await manager.add_resource(r2)
            aws_resources = await manager.list_resources(provider_id="aws1")
            assert len(aws_resources) == 1
            assert aws_resources[0].id == "r1"

    class TestGetResource:
        async def test_get_resource(
            self,
            manager: CloudResourceManager,
            sample_provider: CloudProvider,
            sample_resource: CloudResource,
        ) -> None:
            await manager.register_provider(sample_provider)
            await manager.add_resource(sample_resource)
            resource = await manager.get_resource("res1")
            assert resource.name == "web-server-01"

        async def test_get_resource_not_found(self, manager: CloudResourceManager) -> None:
            with pytest.raises(ProviderNotFoundError):
                await manager.get_resource("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            m = CloudResourceManager()
            assert m.config.discovery_interval_seconds == 3600
            assert m.config.cost_comparison_enabled is True

        def test_custom_config(self) -> None:
            config = CloudConfig(discovery_interval_seconds=7200, default_region="eu-west-1")
            m = CloudResourceManager(config=config)
            assert m.config.discovery_interval_seconds == 7200
            assert m.config.default_region == "eu-west-1"


class TestCloudProviderModel:
    def test_all_provider_types(self) -> None:
        for pt in ProviderType:
            p = CloudProvider(id=pt.value, name=pt.value, provider_type=pt)
            assert p.provider_type == pt

    def test_defaults(self) -> None:
        p = CloudProvider(id="p1", name="Test", provider_type=ProviderType.AZURE)
        assert p.enabled is True
        assert p.region == ""
        assert p.credentials_ref == ""


class TestCloudResourceModel:
    def test_defaults(self) -> None:
        r = CloudResource(id="r1", provider_id="p1", resource_type="vm")
        assert r.status == ResourceStatus.UNKNOWN
        assert r.cost_per_hour == 0.0
        assert r.tags == {}
