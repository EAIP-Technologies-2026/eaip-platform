"""Tests for AuditRuntimeModule."""

from __future__ import annotations

from unittest.mock import MagicMock

from eaip.audit.integration import AuditRuntimeModule
from eaip.audit.models import AuditConfig


class TestAuditRuntimeModule:
    def test_module_name(self) -> None:
        module = AuditRuntimeModule()
        assert module.name == "audit"

    def test_default_config(self) -> None:
        module = AuditRuntimeModule()
        assert module._config.enable_immutable_log is True
        assert module._config.retention_default_days == 90

    def test_custom_config(self) -> None:
        config = AuditConfig(retention_default_days=365, enable_immutable_log=False)
        module = AuditRuntimeModule(config=config)
        assert module._config.retention_default_days == 365
        assert module._config.enable_immutable_log is False

    def test_logger_property(self) -> None:
        module = AuditRuntimeModule()
        assert module.logger is not None

    def test_policy_service_property(self) -> None:
        module = AuditRuntimeModule()
        assert module.policy_service is not None

    def test_classifier_property(self) -> None:
        module = AuditRuntimeModule()
        assert module.classifier is not None

    def test_legal_hold_service_property(self) -> None:
        module = AuditRuntimeModule()
        assert module.legal_hold_service is not None

    async def test_start_stop(self) -> None:
        module = AuditRuntimeModule()
        kernel = MagicMock()
        kernel.platform = MagicMock()
        kernel.platform.capabilities = MagicMock()
        kernel.platform.health = MagicMock()

        await module.start(kernel)
        await module.stop(kernel)

        kernel.platform.capabilities.register.assert_called_once()
        kernel.platform.health.register.assert_called_once()
