"""Organization service — CRUD, hierarchy, members, settings, policies, domains, reports."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from eaip.logging.context import get_logger
from eaip.organization.events import (
    OrganizationActivated,
    OrganizationArchived,
    OrganizationAuditLogged,
    OrganizationCreated,
    OrganizationDeactivated,
    OrganizationDeleted,
    OrganizationDomainsVerified,
    OrganizationMemberAdded,
    OrganizationMemberRemoved,
    OrganizationMemberRoleChanged,
    OrganizationPolicyCreated,
    OrganizationPolicyUpdated,
    OrganizationReportGenerated,
    OrganizationSettingsUpdated,
    OrganizationSubscriptionsUpdated,
    OrganizationUnitAdded,
    OrganizationUnitMoved,
    OrganizationUnitRemoved,
    OrganizationUpdated,
)
from eaip.organization.exceptions import (
    OrganizationDomainError,
    OrganizationError,
    OrganizationMemberError,
    OrganizationNotFoundError,
    OrganizationPolicyError,
    OrganizationSubscriptionError,
    OrganizationUnitError,
)
from eaip.organization.models import (
    Organization,
    OrganizationAuditEntry,
    OrganizationConfig,
    OrganizationContact,
    OrganizationDomain,
    OrganizationFeature,
    OrganizationHierarchy,
    OrganizationMember,
    OrganizationPolicy,
    OrganizationReport,
    OrganizationRole,
    OrganizationSettings,
    OrganizationStatus,
    OrganizationSubscription,
    OrganizationType,
    OrganizationUnit,
    OrganizationUnitType,
)

if TYPE_CHECKING:
    from eaip.events.bus import EventBus


class OrganizationService:
    """Manages organizations — CRUD, hierarchy, members, settings, policies, domains."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize OrganizationService."""
        self._event_bus = event_bus
        self._log = get_logger("eaip.organization.service")
        self._organizations: dict[str, Organization] = {}
        self._hierarchies: dict[str, OrganizationHierarchy] = {}
        self._units: dict[str, OrganizationUnit] = {}
        self._members: dict[str, OrganizationMember] = {}
        self._settings: dict[str, OrganizationSettings] = {}
        self._policies: dict[str, OrganizationPolicy] = {}
        self._domains: dict[str, OrganizationDomain] = {}
        self._subscriptions: dict[str, OrganizationSubscription] = {}
        self._features: dict[str, OrganizationFeature] = {}
        self._contacts: dict[str, OrganizationContact] = {}
        self._configs: dict[str, OrganizationConfig] = {}
        self._audit_logs: dict[str, OrganizationAuditEntry] = {}
        self._reports: dict[str, OrganizationReport] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_organization(
        self,
        name: str,
        slug: str,
        org_type: OrganizationType = OrganizationType.OTHER,
        description: str = "",
        domain: str = "",
        parent_org_id: str | None = None,
    ) -> Organization:
        """Create a new organization."""
        org_id = f"org-{slug}-{len(self._organizations) + 1}"
        org = Organization(
            id=org_id,
            name=name,
            slug=slug,
            org_type=org_type,
            description=description,
            domain=domain,
            parent_org_id=parent_org_id,
        )
        self._organizations[org_id] = org

        if parent_org_id is not None:
            hierarchy = OrganizationHierarchy(
                org_id=org_id,
                ancestor_ids=(parent_org_id,),
                depth=1,
                path=(parent_org_id, org_id),
            )
            self._hierarchies[org_id] = hierarchy
        else:
            self._hierarchies[org_id] = OrganizationHierarchy(org_id=org_id)

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationCreated(
                    org_id=org_id,
                    name=name,
                    slug=slug,
                    org_type=org_type.value,
                )
            )
        self._log.info("organization.created", org_id=org_id)
        return org

    async def get_organization(self, org_id: str) -> Organization:
        """Get an organization by ID.

        Raises:
            OrganizationNotFoundError: If the organization is not found.
        """
        org = self._organizations.get(org_id)
        if org is None:
            raise OrganizationNotFoundError(f"Organization {org_id!r} not found")
        return org

    async def update_organization(self, org_id: str, **changes: Any) -> Organization:
        """Update an organization's attributes.

        Raises:
            OrganizationNotFoundError: If the organization is not found.
        """
        org = await self.get_organization(org_id)
        updated = org.model_copy(update=changes)
        self._organizations[org_id] = updated

        if self._event_bus is not None:
            await self._event_bus.publish(OrganizationUpdated(org_id=org_id, changes=changes))
        self._log.info("organization.updated", org_id=org_id)
        return updated

    async def delete_organization(self, org_id: str, reason: str = "") -> None:
        """Delete an organization.

        Raises:
            OrganizationNotFoundError: If the organization is not found.
        """
        if org_id not in self._organizations:
            raise OrganizationNotFoundError(f"Organization {org_id!r} not found")
        del self._organizations[org_id]
        self._hierarchies.pop(org_id, None)

        if self._event_bus is not None:
            await self._event_bus.publish(OrganizationDeleted(org_id=org_id, reason=reason))
        self._log.info("organization.deleted", org_id=org_id)

    async def list_organizations(
        self, status: OrganizationStatus | None = None
    ) -> list[Organization]:
        """List organizations, optionally filtered by status."""
        orgs = list(self._organizations.values())
        if status is not None:
            orgs = [o for o in orgs if o.status is status]
        return orgs

    async def activate_organization(self, org_id: str) -> Organization:
        """Activate an organization."""
        org = await self.update_organization(org_id, status=OrganizationStatus.ACTIVE)
        if self._event_bus is not None:
            await self._event_bus.publish(OrganizationActivated(org_id=org_id))
        return org

    async def deactivate_organization(self, org_id: str, reason: str = "") -> Organization:
        """Deactivate an organization."""
        org = await self.update_organization(org_id, status=OrganizationStatus.INACTIVE)
        if self._event_bus is not None:
            await self._event_bus.publish(OrganizationDeactivated(org_id=org_id, reason=reason))
        return org

    async def archive_organization(self, org_id: str, reason: str = "") -> Organization:
        """Archive an organization."""
        org = await self.update_organization(org_id, status=OrganizationStatus.ARCHIVED)
        if self._event_bus is not None:
            await self._event_bus.publish(OrganizationArchived(org_id=org_id, reason=reason))
        return org

    # ------------------------------------------------------------------
    # Units
    # ------------------------------------------------------------------

    async def add_unit(
        self,
        org_id: str,
        name: str,
        unit_type: OrganizationUnitType = OrganizationUnitType.OTHER,
        parent_unit_id: str | None = None,
        description: str = "",
        head_user_id: str | None = None,
    ) -> OrganizationUnit:
        """Add a unit to an organization.

        Raises:
            OrganizationNotFoundError: If the organization is not found.
        """
        await self.get_organization(org_id)
        unit_id = f"unit-{org_id}-{len(self._units) + 1}"
        unit = OrganizationUnit(
            id=unit_id,
            org_id=org_id,
            name=name,
            unit_type=unit_type,
            parent_unit_id=parent_unit_id,
            description=description,
            head_user_id=head_user_id,
        )
        self._units[unit_id] = unit

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationUnitAdded(
                    org_id=org_id,
                    unit_id=unit_id,
                    name=name,
                    parent_unit_id=parent_unit_id,
                )
            )
        self._log.info("organization.unit_added", unit_id=unit_id)
        return unit

    async def move_unit(self, unit_id: str, new_parent_id: str | None) -> OrganizationUnit:
        """Move a unit to a new parent.

        Raises:
            OrganizationUnitError: If the unit is not found.
        """
        unit = self._units.get(unit_id)
        if unit is None:
            raise OrganizationUnitError(f"Unit {unit_id!r} not found")
        previous_parent = unit.parent_unit_id
        updated = unit.model_copy(update={"parent_unit_id": new_parent_id})
        self._units[unit_id] = updated

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationUnitMoved(
                    org_id=unit.org_id,
                    unit_id=unit_id,
                    previous_parent_id=previous_parent,
                    new_parent_id=new_parent_id,
                )
            )
        self._log.info("organization.unit_moved", unit_id=unit_id)
        return updated

    async def remove_unit(self, unit_id: str) -> None:
        """Remove a unit.

        Raises:
            OrganizationUnitError: If the unit is not found.
        """
        unit = self._units.get(unit_id)
        if unit is None:
            raise OrganizationUnitError(f"Unit {unit_id!r} not found")
        org_id = unit.org_id
        del self._units[unit_id]

        if self._event_bus is not None:
            await self._event_bus.publish(OrganizationUnitRemoved(org_id=org_id, unit_id=unit_id))
        self._log.info("organization.unit_removed", unit_id=unit_id)

    async def get_unit(self, unit_id: str) -> OrganizationUnit:
        """Get a unit by ID.

        Raises:
            OrganizationUnitError: If the unit is not found.
        """
        unit = self._units.get(unit_id)
        if unit is None:
            raise OrganizationUnitError(f"Unit {unit_id!r} not found")
        return unit

    async def list_units(
        self, org_id: str, unit_type: OrganizationUnitType | None = None
    ) -> list[OrganizationUnit]:
        """List units for an organization, optionally filtered by type."""
        results = [u for u in self._units.values() if u.org_id == org_id]
        if unit_type is not None:
            results = [u for u in results if u.unit_type is unit_type]
        return results

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------

    async def add_member(
        self,
        org_id: str,
        user_id: str,
        email: str,
        name: str = "",
        role: OrganizationRole = OrganizationRole.MEMBER,
    ) -> OrganizationMember:
        """Add a member to an organization.

        Raises:
            OrganizationNotFoundError: If the organization is not found.
            OrganizationMemberError: If the user is already a member.
        """
        await self.get_organization(org_id)
        for existing in self._members.values():
            if existing.org_id == org_id and existing.user_id == user_id:
                raise OrganizationMemberError(
                    f"User {user_id!r} is already a member of organization {org_id!r}"
                )
        member_id = f"mem-{org_id}-{len(self._members) + 1}"
        member = OrganizationMember(
            id=member_id,
            org_id=org_id,
            user_id=user_id,
            email=email,
            name=name,
            role=role,
        )
        self._members[member_id] = member

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationMemberAdded(
                    org_id=org_id,
                    member_id=member_id,
                    user_id=user_id,
                    email=email,
                    role=role.value,
                )
            )
        self._log.info("organization.member_added", member_id=member_id)
        return member

    async def remove_member(self, member_id: str) -> None:
        """Remove a member from an organization.

        Raises:
            OrganizationMemberError: If the member is not found.
        """
        member = self._members.get(member_id)
        if member is None:
            raise OrganizationMemberError(f"Member {member_id!r} not found")
        org_id = member.org_id
        user_id = member.user_id
        del self._members[member_id]

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationMemberRemoved(org_id=org_id, member_id=member_id, user_id=user_id)
            )
        self._log.info("organization.member_removed", member_id=member_id)

    async def change_member_role(
        self, member_id: str, new_role: OrganizationRole
    ) -> OrganizationMember:
        """Change a member's role.

        Raises:
            OrganizationMemberError: If the member is not found.
        """
        member = self._members.get(member_id)
        if member is None:
            raise OrganizationMemberError(f"Member {member_id!r} not found")
        previous_role = member.role
        updated = member.model_copy(update={"role": new_role})
        self._members[member_id] = updated

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationMemberRoleChanged(
                    org_id=member.org_id,
                    member_id=member_id,
                    user_id=member.user_id,
                    previous_role=previous_role.value,
                    new_role=new_role.value,
                )
            )
        self._log.info("organization.member_role_changed", member_id=member_id)
        return updated

    async def get_member(self, member_id: str) -> OrganizationMember:
        """Get a member by ID.

        Raises:
            OrganizationMemberError: If the member is not found.
        """
        member = self._members.get(member_id)
        if member is None:
            raise OrganizationMemberError(f"Member {member_id!r} not found")
        return member

    async def list_members(
        self, org_id: str, role: OrganizationRole | None = None
    ) -> list[OrganizationMember]:
        """List members of an organization, optionally filtered by role."""
        results = [m for m in self._members.values() if m.org_id == org_id]
        if role is not None:
            results = [m for m in results if m.role is role]
        return results

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    async def get_settings(self, org_id: str) -> OrganizationSettings:
        """Get settings for an organization.

        Creates default settings if none exist.
        """
        settings = self._settings.get(org_id)
        if settings is None:
            settings = OrganizationSettings(org_id=org_id)
            self._settings[org_id] = settings
        return settings

    async def update_settings(self, org_id: str, **changes: Any) -> OrganizationSettings:
        """Update organization settings.

        Raises:
            OrganizationNotFoundError: If the organization is not found.
        """
        await self.get_organization(org_id)
        settings = await self.get_settings(org_id)
        updated = settings.model_copy(update=changes)
        self._settings[org_id] = updated

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationSettingsUpdated(org_id=org_id, changes=changes)
            )
        self._log.info("organization.settings_updated", org_id=org_id)
        return updated

    # ------------------------------------------------------------------
    # Policies
    # ------------------------------------------------------------------

    async def create_policy(
        self,
        org_id: str,
        name: str,
        policy_type: str,
        description: str = "",
        rules: dict[str, Any] | None = None,
        priority: int = 0,
    ) -> OrganizationPolicy:
        """Create a policy for an organization.

        Raises:
            OrganizationNotFoundError: If the organization is not found.
        """
        await self.get_organization(org_id)
        policy_id = f"pol-{org_id}-{len(self._policies) + 1}"
        policy = OrganizationPolicy(
            id=policy_id,
            org_id=org_id,
            name=name,
            policy_type=policy_type,
            description=description,
            rules=rules or {},
            priority=priority,
        )
        self._policies[policy_id] = policy

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationPolicyCreated(
                    org_id=org_id,
                    policy_id=policy_id,
                    name=name,
                    policy_type=policy_type,
                )
            )
        self._log.info("organization.policy_created", policy_id=policy_id)
        return policy

    async def update_policy(self, policy_id: str, **changes: Any) -> OrganizationPolicy:
        """Update a policy.

        Raises:
            OrganizationPolicyError: If the policy is not found.
        """
        policy = self._policies.get(policy_id)
        if policy is None:
            raise OrganizationPolicyError(f"Policy {policy_id!r} not found")
        updated = policy.model_copy(update=changes)
        self._policies[policy_id] = updated

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationPolicyUpdated(
                    org_id=policy.org_id,
                    policy_id=policy_id,
                    changes=changes,
                )
            )
        self._log.info("organization.policy_updated", policy_id=policy_id)
        return updated

    async def get_policy(self, policy_id: str) -> OrganizationPolicy:
        """Get a policy by ID.

        Raises:
            OrganizationPolicyError: If the policy is not found.
        """
        policy = self._policies.get(policy_id)
        if policy is None:
            raise OrganizationPolicyError(f"Policy {policy_id!r} not found")
        return policy

    async def list_policies(
        self, org_id: str, policy_type: str | None = None
    ) -> list[OrganizationPolicy]:
        """List policies for an organization, optionally filtered by type."""
        results = [p for p in self._policies.values() if p.org_id == org_id]
        if policy_type is not None:
            results = [p for p in results if p.policy_type == policy_type]
        return results

    # ------------------------------------------------------------------
    # Domains
    # ------------------------------------------------------------------

    async def add_domain(self, org_id: str, domain: str) -> OrganizationDomain:
        """Add a domain to an organization.

        Raises:
            OrganizationDomainError: If the domain already exists for the org.
        """
        for existing in self._domains.values():
            if existing.org_id == org_id and existing.domain == domain:
                raise OrganizationDomainError(
                    f"Domain {domain!r} already exists for organization {org_id!r}"
                )
        domain_id = f"dom-{org_id}-{len(self._domains) + 1}"
        verification_token = f"verify-{domain}-{domain_id}"
        entry = OrganizationDomain(
            id=domain_id,
            org_id=org_id,
            domain=domain,
            verification_token=verification_token,
        )
        self._domains[domain_id] = entry
        self._log.info("organization.domain_added", domain_id=domain_id)
        return entry

    async def verify_domain(self, domain_id: str) -> OrganizationDomain:
        """Verify a domain."""
        entry = self._domains.get(domain_id)
        if entry is None:
            raise OrganizationDomainError(f"Domain entry {domain_id!r} not found")
        updated = entry.model_copy(
            update={
                "verified": True,
                "verified_at": datetime.now(),
            }
        )
        self._domains[domain_id] = updated

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationDomainsVerified(org_id=entry.org_id, domain_ids=(domain_id,))
            )
        self._log.info("organization.domain_verified", domain_id=domain_id)
        return updated

    async def list_domains(
        self, org_id: str, verified: bool | None = None
    ) -> list[OrganizationDomain]:
        """List domains for an organization, optionally filtered by verification status."""
        results = [d for d in self._domains.values() if d.org_id == org_id]
        if verified is not None:
            results = [d for d in results if d.verified is verified]
        return results

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    async def create_subscription(
        self,
        org_id: str,
        plan: str,
        start_date: datetime,
        end_date: datetime | None = None,
        auto_renew: bool = True,
    ) -> OrganizationSubscription:
        """Create a subscription for an organization."""
        sub_id = f"sub-{org_id}-{len(self._subscriptions) + 1}"
        sub = OrganizationSubscription(
            id=sub_id,
            org_id=org_id,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew,
        )
        self._subscriptions[sub_id] = sub
        self._log.info("organization.subscription_created", subscription_id=sub_id)
        return sub

    async def update_subscription(
        self, subscription_id: str, **changes: Any
    ) -> OrganizationSubscription:
        """Update a subscription."""
        sub = self._subscriptions.get(subscription_id)
        if sub is None:
            raise OrganizationSubscriptionError(f"Subscription {subscription_id!r} not found")
        updated = sub.model_copy(update=changes)
        self._subscriptions[subscription_id] = updated

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationSubscriptionsUpdated(
                    org_id=sub.org_id,
                    subscription_id=subscription_id,
                    plan=sub.plan,
                    status=sub.status,
                )
            )
        self._log.info("organization.subscription_updated", subscription_id=subscription_id)
        return updated

    async def get_subscription(self, subscription_id: str) -> OrganizationSubscription:
        """Get a subscription by ID.

        Raises:
            OrganizationSubscriptionError: If the subscription is not found.
        """
        sub = self._subscriptions.get(subscription_id)
        if sub is None:
            raise OrganizationSubscriptionError(f"Subscription {subscription_id!r} not found")
        return sub

    async def list_subscriptions(self, org_id: str) -> list[OrganizationSubscription]:
        """List subscriptions for an organization."""
        return [s for s in self._subscriptions.values() if s.org_id == org_id]

    # ------------------------------------------------------------------
    # Features
    # ------------------------------------------------------------------

    async def set_feature(
        self, org_id: str, feature_key: str, enabled: bool = True
    ) -> OrganizationFeature:
        """Enable or disable a feature for an organization."""
        feature_id = f"feat-{org_id}-{feature_key}"
        feature = OrganizationFeature(
            id=feature_id,
            org_id=org_id,
            feature_key=feature_key,
            enabled=enabled,
        )
        self._features[feature_id] = feature
        self._log.info("organization.feature_set", feature_id=feature_id)
        return feature

    async def get_feature(self, feature_id: str) -> OrganizationFeature:
        """Get a feature by ID."""
        feature = self._features.get(feature_id)
        if feature is None:
            raise OrganizationError(f"Feature {feature_id!r} not found")
        return feature

    async def list_features(self, org_id: str) -> list[OrganizationFeature]:
        """List features for an organization."""
        return [f for f in self._features.values() if f.org_id == org_id]

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    async def add_contact(
        self,
        org_id: str,
        email: str,
        name: str = "",
        phone: str = "",
        title: str = "",
        is_primary: bool = False,
    ) -> OrganizationContact:
        """Add a contact to an organization."""
        contact_id = f"cnt-{org_id}-{len(self._contacts) + 1}"
        contact = OrganizationContact(
            id=contact_id,
            org_id=org_id,
            email=email,
            name=name,
            phone=phone,
            title=title,
            is_primary=is_primary,
        )
        self._contacts[contact_id] = contact
        self._log.info("organization.contact_added", contact_id=contact_id)
        return contact

    async def list_contacts(self, org_id: str) -> list[OrganizationContact]:
        """List contacts for an organization."""
        return [c for c in self._contacts.values() if c.org_id == org_id]

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    async def set_config(
        self, org_id: str, key: str, value: str, description: str = ""
    ) -> OrganizationConfig:
        """Set a configuration value for an organization."""
        config_id = f"cfg-{org_id}-{key}"
        config = OrganizationConfig(
            id=config_id,
            org_id=org_id,
            key=key,
            value=value,
            description=description,
        )
        self._configs[config_id] = config
        self._log.info("organization.config_set", config_id=config_id)
        return config

    async def get_config(self, config_id: str) -> OrganizationConfig:
        """Get a config entry by ID."""
        config = self._configs.get(config_id)
        if config is None:
            raise OrganizationError(f"Config {config_id!r} not found")
        return config

    async def list_configs(self, org_id: str) -> list[OrganizationConfig]:
        """List config entries for an organization."""
        return [c for c in self._configs.values() if c.org_id == org_id]

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    async def log_audit_entry(
        self,
        org_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> OrganizationAuditEntry:
        """Log an audit entry for an organization."""
        entry_id = f"audit-{org_id}-{len(self._audit_logs) + 1}"
        entry = OrganizationAuditEntry(
            id=entry_id,
            org_id=org_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            correlation_id=correlation_id,
        )
        self._audit_logs[entry_id] = entry

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationAuditLogged(
                    org_id=org_id,
                    entry_id=entry_id,
                    actor_id=actor_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                )
            )
        self._log.info("organization.audit_logged", entry_id=entry_id)
        return entry

    async def list_audit_entries(
        self, org_id: str, action: str | None = None
    ) -> list[OrganizationAuditEntry]:
        """List audit entries for an organization, optionally filtered by action."""
        results = [e for e in self._audit_logs.values() if e.org_id == org_id]
        if action is not None:
            results = [e for e in results if e.action == action]
        return results

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    async def generate_report(
        self,
        org_id: str,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
    ) -> OrganizationReport:
        """Generate a report for an organization."""
        report_id = f"rpt-{org_id}-{len(self._reports) + 1}"
        members = await self.list_members(org_id)
        units = await self.list_units(org_id)
        policies = await self.list_policies(org_id)
        report = OrganizationReport(
            id=report_id,
            org_id=org_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            total_members=len(members),
            total_units=len(units),
            total_policies=len(policies),
        )
        self._reports[report_id] = report

        if self._event_bus is not None:
            await self._event_bus.publish(
                OrganizationReportGenerated(
                    org_id=org_id,
                    report_id=report_id,
                    report_type=report_type,
                    period_start=period_start,
                    period_end=period_end,
                )
            )
        self._log.info("organization.report_generated", report_id=report_id)
        return report

    async def get_report(self, report_id: str) -> OrganizationReport:
        """Get a report by ID.

        Raises:
            OrganizationError: If the report is not found.
        """
        report = self._reports.get(report_id)
        if report is None:
            raise OrganizationError(f"Report {report_id!r} not found")
        return report

    async def list_reports(
        self, org_id: str, report_type: str | None = None
    ) -> list[OrganizationReport]:
        """List reports for an organization, optionally filtered by type."""
        results = [r for r in self._reports.values() if r.org_id == org_id]
        if report_type is not None:
            results = [r for r in results if r.report_type == report_type]
        return results
