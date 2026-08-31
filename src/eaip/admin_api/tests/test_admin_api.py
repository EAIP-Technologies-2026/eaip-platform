"""Tests for admin_api package."""

from __future__ import annotations

import pytest

from eaip.admin_api.events import (
    ApiAuditLogged,
    ApiClientActivated,
    ApiClientCreated,
    ApiClientDeactivated,
    ApiClientDeleted,
    ApiClientTokenRotated,
    ApiClientUpdated,
    ApiDefinitionCreated,
    ApiDefinitionDeleted,
    ApiDefinitionUpdated,
    ApiDocumentationGenerated,
    ApiEndpointAdded,
    ApiEndpointRemoved,
    ApiEndpointUpdated,
    ApiUsageMetricCollected,
    ApiVersionDeprecated,
    ApiVersionReleased,
    ApiVersionRetired,
)
from eaip.admin_api.exceptions import (
    AdminApiError,
    ApiAuthError,
    ApiClientError,
    ApiDefinitionNotFoundError,
    ApiEndpointError,
    ApiRateLimitError,
    ApiSpecificationError,
    ApiUsageError,
    ApiVersionError,
)
from eaip.admin_api.models import (
    ApiAuditEntry,
    ApiAuthScheme,
    ApiClient,
    ApiClientPermission,
    ApiClientStatus,
    ApiClientToken,
    ApiDefinition,
    ApiDocumentation,
    ApiEndpoint,
    ApiMethod,
    ApiRateLimit,
    ApiRequest,
    ApiResponse,
    ApiSpecification,
    ApiSwaggerConfig,
    ApiThrottleConfig,
    ApiUsageMetric,
    ApiVersion,
    ApiVersionStatus,
)
from eaip.admin_api.service import AdminApiService


@pytest.fixture
def service() -> AdminApiService:
    return AdminApiService()


def make_definition(**kwargs: str) -> ApiDefinition:
    return ApiDefinition(
        id=kwargs.get("id", "def-1"),
        name=kwargs.get("name", "Test API"),
    )


def make_version(definition_id: str = "def-1", **kwargs: str) -> ApiVersion:
    return ApiVersion(
        id=kwargs.get("id", "ver-1"),
        api_definition_id=definition_id,
        version_string=kwargs.get("version_string", "1.0.0"),
    )


def make_endpoint(definition_id: str = "def-1", **kwargs: str) -> ApiEndpoint:
    return ApiEndpoint(
        id=kwargs.get("id", "ep-1"),
        api_definition_id=definition_id,
        api_version_id=kwargs.get("api_version_id", "ver-1"),
        path=kwargs.get("path", "/test"),
        method=ApiMethod.GET,
    )


def make_client(**kwargs: str) -> ApiClient:
    return ApiClient(
        id=kwargs.get("id", "client-1"),
        name=kwargs.get("name", "Test Client"),
        client_id=kwargs.get("client_id", "c-test-1"),
    )


class TestAdminApiService:
    async def test_create_definition(self, service: AdminApiService) -> None:
        definition = make_definition()
        result = await service.create_definition(definition)
        assert result.id == "def-1"
        assert result.name == "Test API"

    async def test_get_definition(self, service: AdminApiService) -> None:
        definition = make_definition()
        await service.create_definition(definition)
        result = await service.get_definition("def-1")
        assert result.id == "def-1"

    async def test_get_definition_not_found(self, service: AdminApiService) -> None:
        with pytest.raises(ApiDefinitionNotFoundError):
            await service.get_definition("nonexistent")

    async def test_update_definition(self, service: AdminApiService) -> None:
        definition = make_definition()
        await service.create_definition(definition)
        updated = await service.update_definition("def-1", name="Updated API")
        assert updated.name == "Updated API"

    async def test_delete_definition(self, service: AdminApiService) -> None:
        definition = make_definition()
        await service.create_definition(definition)
        await service.delete_definition("def-1")
        with pytest.raises(ApiDefinitionNotFoundError):
            await service.get_definition("def-1")

    async def test_list_definitions(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition(id="def-1", name="API 1"))
        await service.create_definition(make_definition(id="def-2", name="API 2"))
        items = await service.list_definitions()
        assert len(items) == 2

    async def test_create_version(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        version = make_version()
        result = await service.create_version(version)
        assert result.id == "ver-1"

    async def test_get_version(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version())
        result = await service.get_version("def-1", "ver-1")
        assert result.version_string == "1.0.0"

    async def test_list_versions(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version(definition_id="def-1", id="ver-1"))
        await service.create_version(
            make_version(definition_id="def-1", id="ver-2", version_string="2.0.0")
        )
        versions = await service.list_versions("def-1")
        assert len(versions) == 2

    async def test_release_version(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version())
        released = await service.release_version("def-1", "ver-1")
        assert released.status == ApiVersionStatus.RELEASED
        assert released.released_at is not None

    async def test_deprecate_version(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version())
        await service.release_version("def-1", "ver-1")
        deprecated = await service.deprecate_version("def-1", "ver-1")
        assert deprecated.status == ApiVersionStatus.DEPRECATED

    async def test_retire_version(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version())
        await service.release_version("def-1", "ver-1")
        retired = await service.retire_version("def-1", "ver-1")
        assert retired.status == ApiVersionStatus.RETIRED

    async def test_add_endpoint(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version())
        endpoint = make_endpoint()
        result = await service.add_endpoint(endpoint)
        assert result.path == "/test"

    async def test_get_endpoint(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version())
        await service.add_endpoint(make_endpoint())
        result = await service.get_endpoint("def-1", "ep-1")
        assert result.method == ApiMethod.GET

    async def test_update_endpoint(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version())
        await service.add_endpoint(make_endpoint())
        updated = await service.update_endpoint("def-1", "ep-1", path="/updated")
        assert updated.path == "/updated"

    async def test_remove_endpoint(self, service: AdminApiService) -> None:
        await service.create_definition(make_definition())
        await service.create_version(make_version())
        await service.add_endpoint(make_endpoint())
        await service.remove_endpoint("def-1", "ep-1")
        with pytest.raises(ApiEndpointError):
            await service.get_endpoint("def-1", "ep-1")

    async def test_create_client(self, service: AdminApiService) -> None:
        client = make_client()
        result = await service.create_client(client)
        assert result.client_id == "c-test-1"

    async def test_get_client(self, service: AdminApiService) -> None:
        client = make_client()
        await service.create_client(client)
        result = await service.get_client("client-1")
        assert result.name == "Test Client"

    async def test_activate_client(self, service: AdminApiService) -> None:
        client = make_client()
        await service.create_client(client)
        activated = await service.activate_client("client-1")
        assert activated.status == ApiClientStatus.ACTIVE

    async def test_deactivate_client(self, service: AdminApiService) -> None:
        client = make_client()
        await service.create_client(client)
        deactivated = await service.deactivate_client("client-1")
        assert deactivated.status == ApiClientStatus.INACTIVE

    async def test_issue_token(self, service: AdminApiService) -> None:
        client = make_client()
        await service.create_client(client)
        token = ApiClientToken(
            id="tok-1",
            client_id="client-1",
            token_prefix="test",
            token_hash="hash",
        )
        result = await service.issue_token(token)
        assert result.id == "tok-1"

    async def test_rotate_token(self, service: AdminApiService) -> None:
        client = make_client()
        await service.create_client(client)
        old = ApiClientToken(
            id="tok-1",
            client_id="client-1",
            token_prefix="old",
            token_hash="oldhash",
        )
        await service.issue_token(old)
        new = ApiClientToken(
            id="tok-2",
            client_id="client-1",
            token_prefix="new",
            token_hash="newhash",
        )
        result = await service.rotate_token("client-1", "tok-1", new)
        assert result.id == "tok-2"

    async def test_grant_permission(self, service: AdminApiService) -> None:
        client = make_client()
        await service.create_client(client)
        perm = ApiClientPermission(id="perm-1", client_id="client-1", endpoint_id="ep-1")
        result = await service.grant_permission(perm)
        assert result.endpoint_id == "ep-1"

    async def test_generate_documentation(self, service: AdminApiService) -> None:
        definition = make_definition()
        await service.create_definition(definition)
        doc = ApiDocumentation(id="doc-1", api_definition_id="def-1", api_version_id="ver-1")
        result = await service.generate_documentation(doc)
        assert result.format == "markdown"

    async def test_create_specification(self, service: AdminApiService) -> None:
        definition = make_definition()
        await service.create_definition(definition)
        spec = ApiSpecification(id="spec-1", api_definition_id="def-1", api_version_id="ver-1")
        result = await service.create_specification(spec)
        assert result.format == "openapi-3.1"

    async def test_record_usage_metric(self, service: AdminApiService) -> None:
        definition = make_definition()
        await service.create_definition(definition)
        await service.create_version(make_version())
        await service.add_endpoint(make_endpoint())
        metric = ApiUsageMetric(id="m-1", endpoint_id="ep-1", request_count=10, response_count=10)
        result = await service.record_usage_metric(metric)
        assert result.request_count == 10

    async def test_log_audit(self, service: AdminApiService) -> None:
        entry = ApiAuditEntry(
            id="aud-1",
            actor_id="user-1",
            action="delete",
            resource_type="definition",
            resource_id="def-1",
        )
        result = await service.log_audit(entry)
        assert result.actor_id == "user-1"


class TestEventTypes:
    def test_api_definition_created_event_type(self) -> None:
        assert ApiDefinitionCreated.event_type == "eaip.admin_api.api_definition.created"

    def test_api_definition_updated_event_type(self) -> None:
        assert ApiDefinitionUpdated.event_type == "eaip.admin_api.api_definition.updated"

    def test_api_definition_deleted_event_type(self) -> None:
        assert ApiDefinitionDeleted.event_type == "eaip.admin_api.api_definition.deleted"

    def test_api_version_released_event_type(self) -> None:
        assert ApiVersionReleased.event_type == "eaip.admin_api.api_version.released"

    def test_api_version_deprecated_event_type(self) -> None:
        assert ApiVersionDeprecated.event_type == "eaip.admin_api.api_version.deprecated"

    def test_api_version_retired_event_type(self) -> None:
        assert ApiVersionRetired.event_type == "eaip.admin_api.api_version.retired"

    def test_api_endpoint_added_event_type(self) -> None:
        assert ApiEndpointAdded.event_type == "eaip.admin_api.api_endpoint.added"

    def test_api_endpoint_removed_event_type(self) -> None:
        assert ApiEndpointRemoved.event_type == "eaip.admin_api.api_endpoint.removed"

    def test_api_endpoint_updated_event_type(self) -> None:
        assert ApiEndpointUpdated.event_type == "eaip.admin_api.api_endpoint.updated"

    def test_api_client_created_event_type(self) -> None:
        assert ApiClientCreated.event_type == "eaip.admin_api.api_client.created"

    def test_api_client_updated_event_type(self) -> None:
        assert ApiClientUpdated.event_type == "eaip.admin_api.api_client.updated"

    def test_api_client_deleted_event_type(self) -> None:
        assert ApiClientDeleted.event_type == "eaip.admin_api.api_client.deleted"

    def test_api_client_activated_event_type(self) -> None:
        assert ApiClientActivated.event_type == "eaip.admin_api.api_client.activated"

    def test_api_client_deactivated_event_type(self) -> None:
        assert ApiClientDeactivated.event_type == "eaip.admin_api.api_client.deactivated"

    def test_api_client_token_rotated_event_type(self) -> None:
        assert ApiClientTokenRotated.event_type == "eaip.admin_api.api_client.token_rotated"

    def test_api_usage_metric_collected_event_type(self) -> None:
        expected = "eaip.admin_api.usage_metric.collected"
        assert ApiUsageMetricCollected.event_type == expected

    def test_api_audit_logged_event_type(self) -> None:
        assert ApiAuditLogged.event_type == "eaip.admin_api.audit.logged"

    def test_api_documentation_generated_event_type(self) -> None:
        expected = "eaip.admin_api.documentation.generated"
        assert ApiDocumentationGenerated.event_type == expected


class TestExceptions:
    def test_admin_api_error(self) -> None:
        err = AdminApiError("something went wrong")
        assert str(err) == "something went wrong"

    def test_api_definition_not_found_error(self) -> None:
        err = ApiDefinitionNotFoundError("not found")
        assert err.code.value == "EAIP-0003"

    def test_api_endpoint_error(self) -> None:
        err = ApiEndpointError("endpoint error")
        assert err is not None

    def test_api_version_error(self) -> None:
        err = ApiVersionError("version error")
        assert err is not None

    def test_api_client_error(self) -> None:
        err = ApiClientError("client error")
        assert err is not None

    def test_api_auth_error(self) -> None:
        err = ApiAuthError("auth failed")
        assert err.code.value == "EAIP-0020"

    def test_api_rate_limit_error(self) -> None:
        err = ApiRateLimitError("rate limited")
        assert err.code.value == "EAIP-0021"

    def test_api_usage_error(self) -> None:
        err = ApiUsageError("usage error")
        assert err is not None

    def test_api_specification_error(self) -> None:
        err = ApiSpecificationError("spec error")
        assert err is not None


class TestModels:
    def test_api_method_enum(self) -> None:
        assert ApiMethod.GET.value == "GET"
        assert ApiMethod.POST.value == "POST"

    def test_api_auth_scheme_enum(self) -> None:
        assert ApiAuthScheme.API_KEY.value == "api_key"
        assert ApiAuthScheme.BEARER.value == "bearer"

    def test_api_client_status_enum(self) -> None:
        assert ApiClientStatus.ACTIVE.value == "active"
        assert ApiClientStatus.REVOKED.value == "revoked"

    def test_api_version_status_enum(self) -> None:
        assert ApiVersionStatus.DRAFT.value == "draft"
        assert ApiVersionStatus.RETIRED.value == "retired"

    def test_api_definition_frozen(self) -> None:
        d = ApiDefinition(id="d1", name="test")
        assert d.id == "d1"
        assert d.auth_scheme == ApiAuthScheme.API_KEY

    def test_api_version_default_status(self) -> None:
        v = ApiVersion(id="v1", api_definition_id="d1", version_string="1.0.0")
        assert v.status == ApiVersionStatus.DRAFT

    def test_api_endpoint_default_auth(self) -> None:
        ep = ApiEndpoint(
            id="e1",
            api_definition_id="d1",
            api_version_id="v1",
            path="/",
            method=ApiMethod.GET,
        )
        assert ep.auth_required is True

    def test_api_rate_limit_defaults(self) -> None:
        rl = ApiRateLimit()
        assert rl.requests_per_second == 10
        assert rl.burst_size == 20

    def test_api_throttle_config_defaults(self) -> None:
        tc = ApiThrottleConfig()
        assert tc.enabled is True
        assert tc.default_rate_limit == 100

    def test_api_client_default_status(self) -> None:
        c = ApiClient(id="c1", name="test", client_id="cid")
        assert c.status == ApiClientStatus.ACTIVE

    def test_api_swagger_config_defaults(self) -> None:
        sc = ApiSwaggerConfig()
        assert sc.enabled is True
        assert sc.title == "API Documentation"

    def test_api_request_defaults(self) -> None:
        r = ApiRequest(id="r1", endpoint_id="e1", method=ApiMethod.GET, path="/")
        assert r.client_ip == ""

    def test_api_response_defaults(self) -> None:
        r = ApiResponse(id="r1", request_id="req1")
        assert r.status_code == 200
