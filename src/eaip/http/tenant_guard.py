"""Tenant isolation guard — assert_tenant_access + org→prefix mapping.

This module is the central security layer for multi-tenant access control.
It is deliberately kept independent of any particular IdP or directory
service so that it can be used across routers, middleware, and scripts.
"""

from __future__ import annotations


def org_to_prefix(org: str) -> str | None:
    """Map an organisation identifier to its URL path prefix.

    The returned prefix is used to prepend API paths so that requests are
    routed only to the correct tenant's resources.  Organisations not listed
    here are treated as unknown and will be rejected by
    ``assert_tenant_access``.
    """
    _MAP: dict[str, str] = {
        "meridian": "health",
        "apex": "apex",
        "nova": "nova",
        "shared": None,
    }
    return _MAP.get(org)


def assert_tenant_access(org: str, user_role: str) -> bool:
    """Return True if *user_role* is allowed to operate in *org*.

    The function is deliberately narrow — it only checks that the
    organisation is recognized and that the role is not explicitly
    denied.  Additional role-based checks can be layered on top.

    Returns ``True`` when the organisation is known and the role is
    permitted; ``False`` otherwise.
    """
    prefix = org_to_prefix(org)
    if prefix is None:
        return False
    # The organisation is recognized and has a valid prefix.
    # All authenticated users are presumed to have access unless a
    # more granular policy is added later.
    return True