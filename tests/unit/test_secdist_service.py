"""Tests for :mod:`eaip.secdist.distributor`."""

from __future__ import annotations

import pytest

from eaip.secdist.distributor import SecretDistributor
from eaip.secdist.exceptions import TargetNotFoundError
from eaip.secdist.models import (
    DistributionTarget,
    DistributorConfig,
    SecretPackage,
)


class TestSecretDistributor:
    @pytest.fixture
    def distributor(self) -> SecretDistributor:
        return SecretDistributor()

    @pytest.fixture
    def sample_target(self) -> DistributionTarget:
        return DistributionTarget(
            id="target1",
            endpoint="https://example.com/secrets",
            protocol="https",
            auth_method="token",
        )

    @pytest.fixture
    def sample_package(self) -> SecretPackage:
        return SecretPackage(
            id="pkg1",
            name="api-key",
            targets=("target1",),
        )

    class TestRegisterTarget:
        async def test_register_target(
            self, distributor: SecretDistributor, sample_target: DistributionTarget
        ) -> None:
            result = await distributor.register_target(sample_target)
            assert result.id == "target1"
            assert result.endpoint == "https://example.com/secrets"

        async def test_list_targets(
            self, distributor: SecretDistributor, sample_target: DistributionTarget
        ) -> None:
            await distributor.register_target(sample_target)
            targets = await distributor.list_targets()
            assert len(targets) == 1

    class TestGetTarget:
        async def test_get_target(
            self, distributor: SecretDistributor, sample_target: DistributionTarget
        ) -> None:
            await distributor.register_target(sample_target)
            target = await distributor.get_target("target1")
            assert target.endpoint == "https://example.com/secrets"

        async def test_get_target_not_found(self, distributor: SecretDistributor) -> None:
            with pytest.raises(TargetNotFoundError):
                await distributor.get_target("nonexistent")

    class TestDistribute:
        async def test_distribute_secret(
            self,
            distributor: SecretDistributor,
            sample_target: DistributionTarget,
            sample_package: SecretPackage,
        ) -> None:
            await distributor.register_target(sample_target)
            results = await distributor.distribute_secret(sample_package)
            assert len(results) == 1
            assert results[0].success is True
            assert results[0].package_id == "pkg1"

        async def test_distribute_no_target(self, distributor: SecretDistributor) -> None:
            pkg = SecretPackage(id="pkg2", name="key", targets=("missing",))
            results = await distributor.distribute_secret(pkg)
            assert len(results) == 1
            assert results[0].success is False

    class TestHistory:
        async def test_get_distribution_history(
            self,
            distributor: SecretDistributor,
            sample_target: DistributionTarget,
            sample_package: SecretPackage,
        ) -> None:
            await distributor.register_target(sample_target)
            await distributor.distribute_secret(sample_package)
            history = await distributor.get_distribution_history()
            assert len(history) == 1

    class TestRevoke:
        async def test_revoke_distribution(
            self,
            distributor: SecretDistributor,
            sample_target: DistributionTarget,
            sample_package: SecretPackage,
        ) -> None:
            await distributor.register_target(sample_target)
            await distributor.distribute_secret(sample_package)
            result = await distributor.revoke_distribution("pkg1", "target1", "key rotated")
            assert result is True

    class TestCheckStatus:
        async def test_check_status(
            self,
            distributor: SecretDistributor,
            sample_target: DistributionTarget,
            sample_package: SecretPackage,
        ) -> None:
            await distributor.register_target(sample_target)
            await distributor.distribute_secret(sample_package)
            status = await distributor.check_status("pkg1")
            assert status["name"] == "api-key"
            assert status["expired"] is False

        async def test_check_status_not_found(self, distributor: SecretDistributor) -> None:
            with pytest.raises(TargetNotFoundError):
                await distributor.check_status("nonexistent")

    class TestConfig:
        def test_default_config(self) -> None:
            d = SecretDistributor()
            assert d.config.max_retries == 3
            assert d.config.default_ttl_seconds == 3600

        def test_custom_config(self) -> None:
            config = DistributorConfig(max_retries=5, enable_encryption=False)
            d = SecretDistributor(config=config)
            assert d.config.max_retries == 5
            assert d.config.enable_encryption is False
