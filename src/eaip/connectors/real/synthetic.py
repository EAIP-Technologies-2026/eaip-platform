"""M6 synthetic data — pre-populated synthetic connectors and models for development."""

from __future__ import annotations

from typing import Any

from eaip.connectors.capabilities import ConnectorCapabilityRecord, DataClassification
from eaip.connectors.health_tracker import ConnectorHealthReport, DegradationLevel, CircuitState
from eaip.connectors.real.base import ConnectionStatus
from eaip.provider_routing.model_registry import (
    ModelLocality,
    ModelPrivacyLevel,
    ModelRecord,
    ModelStatus,
)
from eaip.shared.time import utc_now


def create_apex_synthetic_connectors() -> list[dict[str, Any]]:
    """Apex Advisory Group synthetic connectors."""
    return [
        {
            "connector_id": "apex-salesforce",
            "tenant_id": "apex-advisory-group",
            "connector_type": "salesforce",
            "name": "Apex Salesforce CRM",
            "description": "Synthetic Salesforce connector for Apex",
            "status": "synthetic",
            "credential_ref": "",
            "capabilities": ["query", "create_record", "update_record", "get_record"],
        },
        {
            "connector_id": "apex-m365",
            "tenant_id": "apex-advisory-group",
            "connector_type": "microsoft365",
            "name": "Apex Microsoft 365",
            "description": "Synthetic M365 connector for Apex",
            "status": "synthetic",
            "credential_ref": "",
            "capabilities": ["list_users", "send_email", "list_events"],
        },
        {
            "connector_id": "apex-slack",
            "tenant_id": "apex-advisory-group",
            "connector_type": "slack",
            "name": "Apex Slack",
            "description": "Synthetic Slack connector for Apex",
            "status": "synthetic",
            "credential_ref": "",
            "capabilities": ["list_channels", "send_message", "list_users"],
        },
    ]


def create_nova_synthetic_connectors() -> list[dict[str, Any]]:
    """Nova Manufacturing Systems synthetic connectors."""
    return [
        {
            "connector_id": "nova-sap",
            "tenant_id": "nova-manufacturing-systems",
            "connector_type": "sap",
            "name": "Nova SAP ERP",
            "description": "Synthetic SAP connector for Nova",
            "status": "synthetic",
            "credential_ref": "",
            "capabilities": ["list_orders", "get_material", "list_vendors"],
        },
        {
            "connector_id": "nova-servicenow",
            "tenant_id": "nova-manufacturing-systems",
            "connector_type": "servicenow",
            "name": "Nova ServiceNow",
            "description": "Synthetic ServiceNow connector for Nova",
            "status": "synthetic",
            "credential_ref": "",
            "capabilities": ["list_incidents", "create_incident", "list_changes"],
        },
        {
            "connector_id": "nova-scada",
            "tenant_id": "nova-manufacturing-systems",
            "connector_type": "rest",
            "name": "Nova SCADA System",
            "description": "Synthetic SCADA connector for Nova",
            "status": "synthetic",
            "credential_ref": "",
            "capabilities": ["get", "post"],
        },
    ]


def create_meridian_synthetic_connectors() -> list[dict[str, Any]]:
    """Meridian Health Services synthetic connectors."""
    return [
        {
            "connector_id": "meridian-ehr",
            "tenant_id": "meridian-health-services",
            "connector_type": "rest",
            "name": "Meridian EHR System",
            "description": "Synthetic EHR connector for Meridian",
            "status": "synthetic",
            "credential_ref": "",
            "capabilities": ["get", "post", "put"],
        },
        {
            "connector_id": "meridian-compliance",
            "tenant_id": "meridian-health-services",
            "connector_type": "servicenow",
            "name": "Meridian Compliance System",
            "description": "Synthetic compliance connector for Meridian",
            "status": "synthetic",
            "credential_ref": "",
            "capabilities": ["list_incidents", "create_incident"],
        },
    ]


def create_synthetic_capability_records() -> list[ConnectorCapabilityRecord]:
    """Create synthetic capability records for all tenants."""
    records = []
    for conn in create_apex_synthetic_connectors() + create_nova_synthetic_connectors() + create_meridian_synthetic_connectors():
        records.append(ConnectorCapabilityRecord(
            connector_id=conn["connector_id"],
            tenant_id=conn["tenant_id"],
            connector_type=conn["connector_type"],
            capabilities=conn["capabilities"],
            operations=conn["capabilities"],
            permissions=[f"{conn['connector_type']}:read"],
            data_classes=["synthetic"],
            data_classification=DataClassification.INTERNAL,
            cost_estimate=0.0,
            latency_estimate_ms=50.0,
            health_status="synthetic",
            tenant_availability=True,
        ))
    return records


def create_synthetic_health_reports() -> list[ConnectorHealthReport]:
    """Create synthetic health reports for all connectors."""
    reports = []
    for conn in create_apex_synthetic_connectors() + create_nova_synthetic_connectors() + create_meridian_synthetic_connectors():
        reports.append(ConnectorHealthReport(
            connector_id=conn["connector_id"],
            tenant_id=conn["tenant_id"],
            availability=0.0,
            latency_ms=0.0,
            error_rate=0.0,
            auth_status="synthetic",
            rate_limit_remaining=-1,
            degradation_level=DegradationLevel.NONE,
            circuit_state=CircuitState.CLOSED,
            consecutive_failures=0,
        ))
    return reports


def create_synthetic_models() -> list[ModelRecord]:
    """Create synthetic model registry entries."""
    now = utc_now()
    return [
        ModelRecord(
            id="openai-gpt4o",
            tenant_id="apex-advisory-group",
            provider="openai",
            model_name="gpt-4o",
            version="2024-08-06",
            capabilities=["chat", "function_calling", "vision", "code_generation"],
            context_limit=128000,
            latency_avg_ms=800.0,
            cost_per_1k_tokens=0.005,
            quality_score=0.95,
            availability=0.99,
            privacy_level=ModelPrivacyLevel.PUBLIC,
            locality=ModelLocality.CLOUD,
            supported_tools=["function_calling"],
            supported_modalities=["text", "image"],
            status=ModelStatus.ACTIVE,
            created_at=now,
        ),
        ModelRecord(
            id="anthropic-claude35",
            tenant_id="apex-advisory-group",
            provider="anthropic",
            model_name="claude-3.5-sonnet",
            version="20241022",
            capabilities=["chat", "function_calling", "code_generation", "analysis"],
            context_limit=200000,
            latency_avg_ms=600.0,
            cost_per_1k_tokens=0.003,
            quality_score=0.93,
            availability=0.98,
            privacy_level=ModelPrivacyLevel.PUBLIC,
            locality=ModelLocality.CLOUD,
            supported_tools=["function_calling"],
            supported_modalities=["text"],
            status=ModelStatus.ACTIVE,
            created_at=now,
        ),
        ModelRecord(
            id="azure-openai-gpt4",
            tenant_id="apex-advisory-group",
            provider="azure_openai",
            model_name="gpt-4",
            version="0613",
            capabilities=["chat", "function_calling", "code_generation"],
            context_limit=8192,
            latency_avg_ms=1000.0,
            cost_per_1k_tokens=0.03,
            quality_score=0.90,
            availability=0.99,
            privacy_level=ModelPrivacyLevel.PRIVATE,
            locality=ModelLocality.CLOUD,
            supported_tools=["function_calling"],
            supported_modalities=["text"],
            status=ModelStatus.ACTIVE,
            created_at=now,
        ),
        ModelRecord(
            id="local-llama3",
            tenant_id="apex-advisory-group",
            provider="ollama",
            model_name="llama3:70b",
            version="1.0",
            capabilities=["chat", "code_generation"],
            context_limit=8192,
            latency_avg_ms=2000.0,
            cost_per_1k_tokens=0.0,
            quality_score=0.75,
            availability=0.95,
            privacy_level=ModelPrivacyLevel.PRIVATE,
            locality=ModelLocality.ON_PREMISE,
            supported_tools=[],
            supported_modalities=["text"],
            status=ModelStatus.ACTIVE,
            created_at=now,
        ),
        ModelRecord(
            id="openai-gpt4o-nova",
            tenant_id="nova-manufacturing-systems",
            provider="openai",
            model_name="gpt-4o",
            version="2024-08-06",
            capabilities=["chat", "function_calling", "vision", "code_generation"],
            context_limit=128000,
            latency_avg_ms=800.0,
            cost_per_1k_tokens=0.005,
            quality_score=0.95,
            availability=0.99,
            privacy_level=ModelPrivacyLevel.PUBLIC,
            locality=ModelLocality.CLOUD,
            supported_tools=["function_calling"],
            supported_modalities=["text", "image"],
            status=ModelStatus.ACTIVE,
            created_at=now,
        ),
        ModelRecord(
            id="azure-openai-gpt4-nova",
            tenant_id="nova-manufacturing-systems",
            provider="azure_openai",
            model_name="gpt-4",
            version="0613",
            capabilities=["chat", "function_calling", "code_generation"],
            context_limit=8192,
            latency_avg_ms=1000.0,
            cost_per_1k_tokens=0.03,
            quality_score=0.90,
            availability=0.99,
            privacy_level=ModelPrivacyLevel.PRIVATE,
            locality=ModelLocality.CLOUD,
            supported_tools=["function_calling"],
            supported_modalities=["text"],
            status=ModelStatus.ACTIVE,
            created_at=now,
        ),
        ModelRecord(
            id="anthropic-claude35-meridian",
            tenant_id="meridian-health-services",
            provider="anthropic",
            model_name="claude-3.5-sonnet",
            version="20241022",
            capabilities=["chat", "function_calling", "code_generation", "analysis"],
            context_limit=200000,
            latency_avg_ms=600.0,
            cost_per_1k_tokens=0.003,
            quality_score=0.93,
            availability=0.98,
            privacy_level=ModelPrivacyLevel.PUBLIC,
            locality=ModelLocality.CLOUD,
            supported_tools=["function_calling"],
            supported_modalities=["text"],
            status=ModelStatus.ACTIVE,
            created_at=now,
        ),
        ModelRecord(
            id="azure-openai-gpt4-meridian",
            tenant_id="meridian-health-services",
            provider="azure_openai",
            model_name="gpt-4",
            version="0613",
            capabilities=["chat", "function_calling", "code_generation"],
            context_limit=8192,
            latency_avg_ms=1000.0,
            cost_per_1k_tokens=0.03,
            quality_score=0.90,
            availability=0.99,
            privacy_level=ModelPrivacyLevel.PRIVATE,
            locality=ModelLocality.CLOUD,
            supported_tools=["function_calling"],
            supported_modalities=["text"],
            status=ModelStatus.ACTIVE,
            created_at=now,
        ),
    ]


def get_all_synthetic_data() -> dict[str, list]:
    """Get all synthetic data for M6."""
    return {
        "connectors": create_apex_synthetic_connectors() + create_nova_synthetic_connectors() + create_meridian_synthetic_connectors(),
        "capabilities": create_synthetic_capability_records(),
        "health_reports": create_synthetic_health_reports(),
        "models": create_synthetic_models(),
    }
