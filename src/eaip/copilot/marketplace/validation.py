"""Server-side package validation engine for EAIP Conductor Marketplace (Phase 5)."""

from __future__ import annotations

import re

from eaip.copilot.marketplace.models import SkillPackageManifest

MIN_PACKAGE_NAME_LENGTH = 3


class PackageValidator:
    """Server-side validator for marketplace skill packages."""

    @staticmethod
    def validate_manifest(manifest: SkillPackageManifest) -> tuple[bool, list[str]]:
        """Validate manifest structure, version format, and security attributes."""
        errors: list[str] = []

        if not manifest.package_id or not re.match(
            r"^[a-zA-Z0-9\._\-]+$", manifest.package_id
        ):
            errors.append(
                "Invalid package_id format. "
                "Must contain alphanumeric, dot, or hyphen characters."
            )

        if not manifest.name or len(manifest.name) < MIN_PACKAGE_NAME_LENGTH:
            errors.append(
                f"Package name must be at least "
                f"{MIN_PACKAGE_NAME_LENGTH} characters long."
            )

        if not re.match(r"^\d+\.\d+\.\d+$", manifest.version):
            errors.append(
                f"Invalid semantic version '{manifest.version}'. "
                "Expected format X.Y.Z."
            )

        if not manifest.skills:
            errors.append("Package must declare at least one skill.")

        invalid_skills = [
            skill for skill in manifest.skills
            if not skill.id or not skill.name
        ]
        if invalid_skills:
            errors.extend(
                f"Skill in package '{manifest.package_id}' is missing "
                "required id or name."
                for _ in invalid_skills
            )

        return len(errors) == 0, errors
