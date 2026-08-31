"""Retrieval policies — access control and policy enforcement for knowledge retrieval."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from eaip.knowledge.models import RetrievedChunk
from eaip.logging.context import get_logger


class AccessLevel(StrEnum):
    """Access levels for knowledge collections."""

    DENY = "deny"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class RetrievalPolicy(BaseModel):
    """Access control policy for a collection or set of collections.

    Defines which subjects (users, roles, groups) can access which
    collections and at what level.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str
    name: str = ""
    description: str = ""
    collections: tuple[str, ...] = Field(default=())
    allowed_subjects: tuple[str, ...] = Field(default=())
    allowed_roles: tuple[str, ...] = Field(default=())
    allowed_groups: tuple[str, ...] = Field(default=())
    access_level: AccessLevel = AccessLevel.READ
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectionAccessPolicy(BaseModel):
    """Maps collections to their access requirements.

    Defines which roles and groups are required to access
    a specific collection.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    collection: str
    required_roles: tuple[str, ...] = Field(default=())
    required_groups: tuple[str, ...] = Field(default=())
    default_access: AccessLevel = AccessLevel.DENY
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class PolicyResolver(Protocol):
    """Protocol for resolving policies for a given context."""

    async def resolve(
        self,
        subject_id: str,
        roles: Sequence[str],
        groups: Sequence[str],
        collection: str,
    ) -> AccessLevel:
        """Resolve the access level for a subject on a collection.

        Args:
            subject_id: The subject identifier.
            roles: The subject's roles.
            groups: The subject's groups.
            collection: The collection name.

        Returns:
            The resolved AccessLevel.
        """
        ...


class RetrievalPolicyEnforcer:
    """Enforces retrieval policies during knowledge search.

    Evaluates access control policies before returning results,
    filtering out chunks from collections the subject cannot access.
    """

    def __init__(
        self,
        policies: Sequence[RetrievalPolicy] | None = None,
        collection_policies: Sequence[CollectionAccessPolicy] | None = None,
        resolver: PolicyResolver | None = None,
    ) -> None:
        """Initialize the enforcer.

        Args:
            policies: Global retrieval policies.
            collection_policies: Per-collection access policies.
            resolver: Optional custom policy resolver.
        """
        self._policies: list[RetrievalPolicy] = list(policies or [])
        self._collection_policies: dict[str, CollectionAccessPolicy] = {
            cp.collection: cp for cp in (collection_policies or [])
        }
        self._resolver = resolver
        self._log = get_logger("eaip.knowledge.policies")

    def add_policy(self, policy: RetrievalPolicy) -> None:
        """Register a retrieval policy.

        Args:
            policy: The policy to add.
        """
        self._policies.append(policy)

    def add_collection_policy(self, policy: CollectionAccessPolicy) -> None:
        """Register a collection access policy.

        Args:
            policy: The collection policy to add.
        """
        self._collection_policies[policy.collection] = policy

    async def check_access(
        self,
        collection: str,
        subject_id: str = "",
        roles: Sequence[str] | None = None,
        groups: Sequence[str] | None = None,
    ) -> bool:
        """Check whether a subject can access a collection.

        Args:
            collection: The collection name.
            subject_id: The subject identifier.
            roles: The subject's roles.
            groups: The subject's groups.

        Returns:
            True if access is allowed, False otherwise.
        """
        roles = roles or []
        groups = groups or []

        if self._resolver is not None:
            level = await self._resolver.resolve(subject_id, roles, groups, collection)
            return level is not AccessLevel.DENY

        collection_explicitly_covered = False
        for policy in self._policies:
            if collection in policy.collections:
                collection_explicitly_covered = True
                if self._subject_matches(policy, subject_id, roles, groups):
                    return policy.access_level is not AccessLevel.DENY

        if collection_explicitly_covered:
            return False

        for policy in self._policies:
            if not policy.collections and self._subject_matches(policy, subject_id, roles, groups):
                return policy.access_level is not AccessLevel.DENY

        cp = self._collection_policies.get(collection)
        if cp is not None:
            if cp.default_access is AccessLevel.DENY:
                has_role = any(r in cp.required_roles for r in roles)
                has_group = any(g in cp.required_groups for g in groups)
                return has_role or has_group
            return True

        return True

    async def filter_results(
        self,
        chunks: Sequence[RetrievedChunk],
        subject_id: str = "",
        roles: Sequence[str] | None = None,
        groups: Sequence[str] | None = None,
    ) -> tuple[RetrievedChunk, ...]:
        """Filter retrieved chunks based on access policies.

        Args:
            chunks: The retrieved chunks to filter.
            subject_id: The subject identifier.
            roles: The subject's roles.
            groups: The subject's groups.

        Returns:
            A tuple of chunks the subject can access.

        Raises:
            RetrievalError: If policy resolution fails.
        """
        roles = roles or []
        groups = groups or []
        allowed: list[RetrievedChunk] = []

        for chunk in chunks:
            try:
                if await self.check_access(chunk.collection, subject_id, roles, groups):
                    allowed.append(chunk)
            except Exception as exc:
                self._log.warning(
                    "policies.filter_results.check_failed",
                    collection=chunk.collection,
                    chunk_id=chunk.chunk_id,
                    error=str(exc),
                )

        return tuple(allowed)

    @staticmethod
    def _subject_matches(
        policy: RetrievalPolicy,
        subject_id: str,
        roles: Sequence[str],
        groups: Sequence[str],
    ) -> bool:
        if subject_id and subject_id in policy.allowed_subjects:
            return True
        if any(r in policy.allowed_roles for r in roles):
            return True
        return bool(any(g in policy.allowed_groups for g in groups))


__all__ = [
    "AccessLevel",
    "CollectionAccessPolicy",
    "PolicyResolver",
    "RetrievalPolicy",
    "RetrievalPolicyEnforcer",
]
