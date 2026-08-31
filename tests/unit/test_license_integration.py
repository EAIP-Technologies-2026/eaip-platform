"""Tests for :mod:`eaip.license.integration` and :mod:`eaip.license.health`."""

from __future__ import annotations

import pytest

from eaip.license.enforcement import LicenseEnforcer
from eaip.license.health import LicenseHealthCheck
from eaip.license.integration import LicenseRuntimeModule
from eaip.license.manager import LicenseManager
from eaip.license.models import LicenseConfig


class TestLicenseRuntimeModule:
    def test_instantiation(self) -> None:
        module = LicenseRuntimeModule()
        assert module.name == "license"
        assert isinstance(module.config, LicenseConfig)
        assert isinstance(module.manager, LicenseManager)
        assert isinstance(module.enforcer, LicenseEnforcer)
        assert isinstance(module.health_check, LicenseHealthCheck)

    def test_custom_services(self) -> None:
        config = LicenseConfig(enable_offline_validation=False)
        manager = LicenseManager(config=config)
        enforcer = LicenseEnforcer(manager)
        module = LicenseRuntimeModule(
            config=config,
            manager=manager,
            enforcer=enforcer,
        )
        assert module.config.enable_offline_validation is False
        assert module.manager is manager
        assert module.enforcer is enforcer

    def test_enforcer_uses_manager(self) -> None:
        module = LicenseRuntimeModule()
        assert module.enforcer._manager is module.manager


class TestLicenseHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_healthy(self) -> None:
        module = LicenseRuntimeModule()
        report = await module.health_check.check()
        assert report.component == "license"
        assert report.status.value == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_details(self) -> None:
        module = LicenseRuntimeModule()
        await module.manager.create_license("Test", "key-1")
        report = await module.health_check.check()
        assert "license_count" in report.details
        assert report.details["license_count"] == 1

    @pytest.mark.asyncio
    async def test_health_check_active_count(self) -> None:
        module = LicenseRuntimeModule()
        await module.manager.create_license("A", "key-a")
        await module.manager.create_license("B", "key-b")
        report = await module.health_check.check()
        assert report.details["active_count"] == 2

    @pytest.mark.asyncio
    async def test_health_check_revoked_count(self) -> None:
        module = LicenseRuntimeModule()
        lic = await module.manager.create_license("Test", "key-1")
        await module.manager.revoke_license(lic.id)
        report = await module.health_check.check()
        assert report.details["revoked_count"] == 1

    @pytest.mark.asyncio
    async def test_health_check_message(self) -> None:
        module = LicenseRuntimeModule()
        report = await module.health_check.check()
        assert "healthy" in report.message

    @pytest.mark.asyncio
    async def test_health_check_no_active_licenses(self) -> None:
        module = LicenseRuntimeModule()
        lic = await module.manager.create_license("Test", "key-1")
        await module.manager.revoke_license(lic.id)
        report = await module.health_check.check()
        assert report.status.value == "degraded"
        assert "No active licenses" in report.message
