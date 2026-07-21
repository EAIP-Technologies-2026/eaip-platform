"""AdminApiService — manage API definitions, versions, endpoints, clients, tokens, documentation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

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
    ApiClientError,
    ApiDefinitionNotFoundError,
    ApiEndpointError,
    ApiSpecificationError,
    ApiVersionError,
)
from eaip.admin_api.models import (
    ApiAuditEntry,
    ApiClient,
    ApiClientPermission,
    ApiClientStatus,
    ApiClientToken,
    ApiDefinition,
    ApiDocumentation,
    ApiEndpoint,
    ApiSpecification,
    ApiUsageMetric,
    ApiVersion,
    ApiVersionStatus,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class AdminApiService:
    """Service for managing administrative API definitions, versions, endpoints, and clients."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize AdminApiService."""
        self._definitions: dict[str, ApiDefinition] = {}
        self._versions: dict[str, list[ApiVersion]] = {}
        self._endpoints: dict[str, list[ApiEndpoint]] = {}
        self._clients: dict[str, ApiClient] = {}
        self._client_tokens: dict[str, list[ApiClientToken]] = {}
        self._client_permissions: dict[str, list[ApiClientPermission]] = {}
        self._usage_metrics: dict[str, list[ApiUsageMetric]] = {}
        self._audit_entries: dict[str, list[ApiAuditEntry]] = {}
        self._documentation: dict[str, ApiDocumentation] = {}
        self._specifications: dict[str, ApiSpecification] = {}
        self._event_bus = event_bus or EventBus()
        self._log = get_logger("eaip.admin_api.service")

    # -- API Definitions ---------------------------------------------------

    async def create_definition(self, definition: ApiDefinition) -> ApiDefinition:
        if definition.id in self._definitions:
            raise ApiDefinitionNotFoundError(f"definition already exists: {definition.id!r}")
        self._definitions[definition.id] = definition
        await self._event_bus.publish(
            ApiDefinitionCreated(
                api_definition_id=definition.id,
                name=definition.name,
            )
        )
        self._log.info("admin_api.definition.created", id=definition.id)
        return definition

    async def get_definition(self, definition_id: str) -> ApiDefinition:
        definition = self._definitions.get(definition_id)
        if definition is None:
            raise ApiDefinitionNotFoundError(f"definition not found: {definition_id!r}")
        return definition

    async def update_definition(self, definition_id: str, **kwargs: Any) -> ApiDefinition:
        existing = await self.get_definition(definition_id)
        updated = existing.__class__(
            id=existing.id,
            name=kwargs.get("name", existing.name),
            description=kwargs.get("description", existing.description),
            base_path=kwargs.get("base_path", existing.base_path),
            version=kwargs.get("version", existing.version),
            auth_scheme=kwargs.get("auth_scheme", existing.auth_scheme),
            metadata=kwargs.get("metadata", existing.metadata),
            created_at=existing.created_at,
            updated_at=utc_now(),
        )
        self._definitions[definition_id] = updated
        await self._event_bus.publish(
            ApiDefinitionUpdated(
                api_definition_id=definition_id,
                name=updated.name,
            )
        )
        self._log.info("admin_api.definition.updated", id=definition_id)
        return updated

    async def delete_definition(self, definition_id: str) -> None:
        definition = await self.get_definition(definition_id)
        del self._definitions[definition_id]
        self._versions.pop(definition_id, None)
        self._endpoints.pop(definition_id, None)
        await self._event_bus.publish(
            ApiDefinitionDeleted(
                api_definition_id=definition_id,
                name=definition.name,
            )
        )
        self._log.info("admin_api.definition.deleted", id=definition_id)

    async def list_definitions(self) -> list[ApiDefinition]:
        return list(self._definitions.values())

    # -- API Versions ------------------------------------------------------

    async def create_version(self, version: ApiVersion) -> ApiVersion:
        await self.get_definition(version.api_definition_id)
        versions = self._versions.setdefault(version.api_definition_id, [])
        versions.append(version)
        await self._event_bus.publish(
            ApiVersionReleased(
                version_id=version.id,
                api_definition_id=version.api_definition_id,
                version_string=version.version_string,
            )
        )
        self._log.info(
            "admin_api.version.created",
            id=version.id,
            definition_id=version.api_definition_id,
        )
        return version

    async def get_version(self, definition_id: str, version_id: str) -> ApiVersion:
        await self.get_definition(definition_id)
        versions = self._versions.get(definition_id, [])
        for v in versions:
            if v.id == version_id:
                return v
        raise ApiVersionError(f"version not found: {version_id!r}")

    async def list_versions(self, definition_id: str) -> list[ApiVersion]:
        await self.get_definition(definition_id)
        return list(self._versions.get(definition_id, []))

    async def release_version(self, definition_id: str, version_id: str) -> ApiVersion:
        version = await self.get_version(definition_id, version_id)
        if version.status != ApiVersionStatus.DRAFT:
            raise ApiVersionError(f"cannot release version in status {version.status.value}")
        updated = version.__class__(
            id=version.id,
            api_definition_id=version.api_definition_id,
            version_string=version.version_string,
            status=ApiVersionStatus.RELEASED,
            released_at=utc_now(),
            deprecated_at=version.deprecated_at,
            retired_at=version.retired_at,
            changelog=version.changelog,
            metadata=version.metadata,
            created_at=version.created_at,
        )
        await self._replace_version(definition_id, updated)
        await self._event_bus.publish(
            ApiVersionReleased(
                version_id=version_id,
                api_definition_id=definition_id,
                version_string=updated.version_string,
            )
        )
        self._log.info("admin_api.version.released", id=version_id)
        return updated

    async def deprecate_version(
        self,
        definition_id: str,
        version_id: str,
        sunset_at: datetime | None = None,
    ) -> ApiVersion:
        version = await self.get_version(definition_id, version_id)
        updated = version.__class__(
            id=version.id,
            api_definition_id=version.api_definition_id,
            version_string=version.version_string,
            status=ApiVersionStatus.DEPRECATED,
            released_at=version.released_at,
            deprecated_at=utc_now(),
            retired_at=version.retired_at,
            changelog=version.changelog,
            metadata=version.metadata,
            created_at=version.created_at,
        )
        await self._replace_version(definition_id, updated)
        await self._event_bus.publish(
            ApiVersionDeprecated(
                version_id=version_id,
                api_definition_id=definition_id,
                version_string=updated.version_string,
                sunset_at=sunset_at,
            )
        )
        self._log.info("admin_api.version.deprecated", id=version_id)
        return updated

    async def retire_version(self, definition_id: str, version_id: str) -> ApiVersion:
        version = await self.get_version(definition_id, version_id)
        updated = version.__class__(
            id=version.id,
            api_definition_id=version.api_definition_id,
            version_string=version.version_string,
            status=ApiVersionStatus.RETIRED,
            released_at=version.released_at,
            deprecated_at=version.deprecated_at,
            retired_at=utc_now(),
            changelog=version.changelog,
            metadata=version.metadata,
            created_at=version.created_at,
        )
        await self._replace_version(definition_id, updated)
        await self._event_bus.publish(
            ApiVersionRetired(
                version_id=version_id,
                api_definition_id=definition_id,
                version_string=updated.version_string,
            )
        )
        self._log.info("admin_api.version.retired", id=version_id)
        return updated

    async def _replace_version(self, definition_id: str, version: ApiVersion) -> None:
        versions = self._versions.get(definition_id, [])
        self._versions[definition_id] = [v if v.id != version.id else version for v in versions]

    # -- API Endpoints -----------------------------------------------------

    async def add_endpoint(self, endpoint: ApiEndpoint) -> ApiEndpoint:
        await self.get_definition(endpoint.api_definition_id)
        await self.get_version(endpoint.api_definition_id, endpoint.api_version_id)
        endpoints = self._endpoints.setdefault(endpoint.api_definition_id, [])
        endpoints.append(endpoint)
        await self._event_bus.publish(
            ApiEndpointAdded(
                endpoint_id=endpoint.id,
                api_definition_id=endpoint.api_definition_id,
                api_version_id=endpoint.api_version_id,
                path=endpoint.path,
                method=endpoint.method.value,
            )
        )
        self._log.info("admin_api.endpoint.added", id=endpoint.id)
        return endpoint

    async def get_endpoint(self, definition_id: str, endpoint_id: str) -> ApiEndpoint:
        await self.get_definition(definition_id)
        endpoints = self._endpoints.get(definition_id, [])
        for ep in endpoints:
            if ep.id == endpoint_id:
                return ep
        raise ApiEndpointError(f"endpoint not found: {endpoint_id!r}")

    async def list_endpoints(self, definition_id: str) -> list[ApiEndpoint]:
        await self.get_definition(definition_id)
        return list(self._endpoints.get(definition_id, []))

    async def update_endpoint(
        self,
        definition_id: str,
        endpoint_id: str,
        **kwargs: Any,
    ) -> ApiEndpoint:
        existing = await self.get_endpoint(definition_id, endpoint_id)
        updated = existing.__class__(
            id=existing.id,
            api_definition_id=existing.api_definition_id,
            api_version_id=kwargs.get("api_version_id", existing.api_version_id),
            path=kwargs.get("path", existing.path),
            method=kwargs.get("method", existing.method),
            description=kwargs.get("description", existing.description),
            request_schema=kwargs.get("request_schema", existing.request_schema),
            response_schema=kwargs.get("response_schema", existing.response_schema),
            auth_required=kwargs.get("auth_required", existing.auth_required),
            rate_limit=kwargs.get("rate_limit", existing.rate_limit),
            tags=kwargs.get("tags", existing.tags),
            metadata=kwargs.get("metadata", existing.metadata),
        )
        endpoints = self._endpoints.get(definition_id, [])
        self._endpoints[definition_id] = [
            ep if ep.id != endpoint_id else updated for ep in endpoints
        ]
        await self._event_bus.publish(
            ApiEndpointUpdated(
                endpoint_id=endpoint_id,
                api_definition_id=definition_id,
                api_version_id=updated.api_version_id,
                path=updated.path,
                method=updated.method.value,
            )
        )
        self._log.info("admin_api.endpoint.updated", id=endpoint_id)
        return updated

    async def remove_endpoint(self, definition_id: str, endpoint_id: str) -> None:
        await self.get_endpoint(definition_id, endpoint_id)
        endpoints = self._endpoints.get(definition_id, [])
        self._endpoints[definition_id] = [ep for ep in endpoints if ep.id != endpoint_id]
        await self._event_bus.publish(
            ApiEndpointRemoved(
                endpoint_id=endpoint_id,
                api_definition_id=definition_id,
                api_version_id="",
            )
        )
        self._log.info("admin_api.endpoint.removed", id=endpoint_id)

    # -- API Clients -------------------------------------------------------

    async def create_client(self, client: ApiClient) -> ApiClient:
        if client.id in self._clients:
            raise ApiClientError(f"client already exists: {client.id!r}")
        self._clients[client.id] = client
        await self._event_bus.publish(
            ApiClientCreated(
                client_id=client.id,
                name=client.name,
                client_id_str=client.client_id,
            )
        )
        self._log.info("admin_api.client.created", id=client.id)
        return client

    async def get_client(self, client_id: str) -> ApiClient:
        client = self._clients.get(client_id)
        if client is None:
            raise ApiClientError(f"client not found: {client_id!r}")
        return client

    async def update_client(self, client_id: str, **kwargs: Any) -> ApiClient:
        existing = await self.get_client(client_id)
        updated = existing.__class__(
            id=existing.id,
            name=kwargs.get("name", existing.name),
            description=kwargs.get("description", existing.description),
            client_id=existing.client_id,
            status=kwargs.get("status", existing.status),
            permissions=kwargs.get("permissions", existing.permissions),
            rate_limit_config=kwargs.get("rate_limit_config", existing.rate_limit_config),
            created_at=existing.created_at,
            updated_at=utc_now(),
            last_used_at=existing.last_used_at,
            metadata=kwargs.get("metadata", existing.metadata),
        )
        self._clients[client_id] = updated
        await self._event_bus.publish(ApiClientUpdated(client_id=client_id, name=updated.name))
        self._log.info("admin_api.client.updated", id=client_id)
        return updated

    async def delete_client(self, client_id: str) -> None:
        client = await self.get_client(client_id)
        del self._clients[client_id]
        self._client_tokens.pop(client_id, None)
        self._client_permissions.pop(client_id, None)
        await self._event_bus.publish(ApiClientDeleted(client_id=client_id, name=client.name))
        self._log.info("admin_api.client.deleted", id=client_id)

    async def list_clients(self) -> list[ApiClient]:
        return list(self._clients.values())

    async def activate_client(self, client_id: str) -> ApiClient:
        await self.get_client(client_id)
        updated = await self.update_client(client_id, status=ApiClientStatus.ACTIVE)
        await self._event_bus.publish(ApiClientActivated(client_id=client_id))
        self._log.info("admin_api.client.activated", id=client_id)
        return updated

    async def deactivate_client(self, client_id: str) -> ApiClient:
        await self.get_client(client_id)
        updated = await self.update_client(client_id, status=ApiClientStatus.INACTIVE)
        await self._event_bus.publish(ApiClientDeactivated(client_id=client_id))
        self._log.info("admin_api.client.deactivated", id=client_id)
        return updated

    # -- Client Tokens -----------------------------------------------------

    async def issue_token(self, token: ApiClientToken) -> ApiClientToken:
        await self.get_client(token.client_id)
        tokens = self._client_tokens.setdefault(token.client_id, [])
        tokens.append(token)
        self._log.info("admin_api.token.issued", id=token.id, client_id=token.client_id)
        return token

    async def rotate_token(
        self,
        client_id: str,
        token_id: str,
        new_token: ApiClientToken,
    ) -> ApiClientToken:
        await self.get_client(client_id)
        tokens = self._client_tokens.get(client_id, [])
        for t in tokens:
            if t.id == token_id:
                self._client_tokens[client_id] = [tkn for tkn in tokens if tkn.id != token_id]
                break
        self._client_tokens.setdefault(client_id, []).append(new_token)
        await self._event_bus.publish(ApiClientTokenRotated(client_id=client_id, token_id=token_id))
        self._log.info("admin_api.token.rotated", old_token_id=token_id, client_id=client_id)
        return new_token

    async def list_tokens(self, client_id: str) -> list[ApiClientToken]:
        await self.get_client(client_id)
        return list(self._client_tokens.get(client_id, []))

    async def revoke_token(self, client_id: str, token_id: str) -> None:
        await self.get_client(client_id)
        tokens = self._client_tokens.get(client_id, [])
        self._client_tokens[client_id] = [t for t in tokens if t.id != token_id]
        self._log.info("admin_api.token.revoked", id=token_id, client_id=client_id)

    # -- Client Permissions ------------------------------------------------

    async def grant_permission(self, permission: ApiClientPermission) -> ApiClientPermission:
        await self.get_client(permission.client_id)
        perms = self._client_permissions.setdefault(permission.client_id, [])
        perms.append(permission)
        self._log.info(
            "admin_api.permission.granted",
            client_id=permission.client_id,
            endpoint_id=permission.endpoint_id,
        )
        return permission

    async def list_permissions(self, client_id: str) -> list[ApiClientPermission]:
        await self.get_client(client_id)
        return list(self._client_permissions.get(client_id, []))

    # -- Documentation -----------------------------------------------------

    async def generate_documentation(self, documentation: ApiDocumentation) -> ApiDocumentation:
        await self.get_definition(documentation.api_definition_id)
        self._documentation[documentation.id] = documentation
        await self._event_bus.publish(
            ApiDocumentationGenerated(
                documentation_id=documentation.id,
                api_definition_id=documentation.api_definition_id,
                api_version_id=documentation.api_version_id,
                format=documentation.format,
            )
        )
        self._log.info("admin_api.documentation.generated", id=documentation.id)
        return documentation

    async def get_documentation(self, documentation_id: str) -> ApiDocumentation:
        doc = self._documentation.get(documentation_id)
        if doc is None:
            raise ApiSpecificationError(f"documentation not found: {documentation_id!r}")
        return doc

    # -- Specifications ----------------------------------------------------

    async def create_specification(self, specification: ApiSpecification) -> ApiSpecification:
        await self.get_definition(specification.api_definition_id)
        self._specifications[specification.id] = specification
        self._log.info("admin_api.specification.created", id=specification.id)
        return specification

    async def get_specification(self, specification_id: str) -> ApiSpecification:
        spec = self._specifications.get(specification_id)
        if spec is None:
            raise ApiSpecificationError(f"specification not found: {specification_id!r}")
        return spec

    # -- Usage Metrics -----------------------------------------------------

    async def record_usage_metric(self, metric: ApiUsageMetric) -> ApiUsageMetric:
        metrics = self._usage_metrics.setdefault(metric.endpoint_id, [])
        metrics.append(metric)
        await self._event_bus.publish(
            ApiUsageMetricCollected(
                metric_id=metric.id,
                endpoint_id=metric.endpoint_id,
                request_count=metric.request_count,
                response_count=metric.response_count,
            )
        )
        self._log.info("admin_api.usage_metric.recorded", id=metric.id)
        return metric

    async def get_usage_metrics(self, endpoint_id: str) -> list[ApiUsageMetric]:
        return list(self._usage_metrics.get(endpoint_id, []))

    # -- Audit -------------------------------------------------------------

    async def log_audit(self, entry: ApiAuditEntry) -> ApiAuditEntry:
        entries = self._audit_entries.setdefault(entry.resource_type, [])
        entries.append(entry)
        await self._event_bus.publish(
            ApiAuditLogged(
                entry_id=entry.id,
                actor_id=entry.actor_id,
                action=entry.action,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                outcome=entry.outcome,
            )
        )
        self._log.info("admin_api.audit.logged", id=entry.id)
        return entry

    async def get_audit_entries(self, resource_type: str) -> list[ApiAuditEntry]:
        return list(self._audit_entries.get(resource_type, []))


__all__ = ["AdminApiService"]
