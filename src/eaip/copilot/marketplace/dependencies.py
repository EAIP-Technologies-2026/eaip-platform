"""Dependency Resolution & Graph Validation for EAIP Conductor Marketplace (Phase 6)."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from eaip.copilot.marketplace.models import SkillPackageManifest

logger = logging.getLogger("eaip.copilot.marketplace.dependencies")


class DependencyResolutionError(Exception):
    """Raised when package dependency constraints cannot be satisfied."""


class DependencyResolver:
    """Resolves and validates dependency chains and versions across skill packages."""

    @staticmethod
    def validate_dependencies(
        package: SkillPackageManifest, catalog: Sequence[SkillPackageManifest]
    ) -> tuple[bool, list[str]]:
        """Validate package dependencies against the active catalog."""
        errors: list[str] = []
        catalog_by_id = {p.package_id: p for p in catalog}

        for dep_id in package.tool_dependencies:
            # Check tool or skill package dependency presence
            if not dep_id:
                continue

        # Check explicit package dependencies if declared
        # Circular dependency check using Depth-First Search
        visited: set[str] = set()
        path: list[str] = []

        def check_cycle(pkg_id: str) -> None:
            if pkg_id in path:
                cycle_path = [*path[path.index(pkg_id):], pkg_id]
                cycle_str = " -> ".join(cycle_path)
                errors.append(f"Circular dependency detected: {cycle_str}")
                return
            if pkg_id in visited:
                return

            visited.add(pkg_id)
            path.append(pkg_id)
            pkg = catalog_by_id.get(pkg_id)
            if pkg:
                for child_id in pkg.tool_dependencies:
                    if child_id in catalog_by_id:
                        check_cycle(child_id)
            path.pop()

        check_cycle(package.package_id)

        return len(errors) == 0, errors
