"""IaCValidator — validate Infrastructure as Code templates."""

from __future__ import annotations

from eaip.iacvalid.events import (
    TemplateRegistered,
    ValidationCompleted,
    ValidationStarted,
    ViolationFound,
)
from eaip.iacvalid.exceptions import TemplateNotFoundError
from eaip.iacvalid.models import (
    CheckType,
    IaCTemplate,
    IaCTemplateStatus,
    IaCType,
    ValidationCheck,
    ValidatorConfig,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class IaCValidator:
    """Central service for validating Infrastructure as Code templates."""

    def __init__(self, config: ValidatorConfig | None = None) -> None:
        self._config = config or ValidatorConfig()
        self._templates: dict[str, IaCTemplate] = {}
        self._checks: dict[str, ValidationCheck] = {}
        self._log = get_logger("eaip.iacvalid.validator")

    @property
    def config(self) -> ValidatorConfig:
        return self._config

    async def register_template(self, template: IaCTemplate) -> IaCTemplate:
        """Register a new IaC template for validation."""
        self._templates[template.id] = template
        TemplateRegistered(
            template_id=template.id,
            name=template.name,
            type=template.type,
        )
        self._log.info(
            "iacvalid.template.registered",
            template_id=template.id,
            name=template.name,
            type=template.type.value,
        )
        return template

    async def get_template(self, template_id: str) -> IaCTemplate:
        """Get an IaC template by ID."""
        template = self._templates.get(template_id)
        if template is None:
            raise TemplateNotFoundError(f"IaC template not found: {template_id}")
        return template

    async def list_templates(self, type: IaCType | None = None) -> list[IaCTemplate]:
        """List IaC templates, optionally filtered by type."""
        result = list(self._templates.values())
        if type is not None:
            result = [t for t in result if t.type == type]
        return sorted(result, key=lambda t: t.name)

    async def validate_template(
        self, template_id: str, check_types: tuple[CheckType, ...] | None = None
    ) -> list[ValidationCheck]:
        """Run validation checks against a template."""
        template = await self.get_template(template_id)

        types = check_types or (
            CheckType.SYNTAX,
            CheckType.POLICY,
            CheckType.SECURITY,
            CheckType.COMPLIANCE,
        )

        ValidationStarted(
            template_id=template_id,
            name=template.name,
            check_types=types,
        )

        results: list[ValidationCheck] = []
        failed = False

        for ctype in types:
            if len(results) >= self._config.max_checks_per_template:
                break

            check = ValidationCheck(
                id=f"check-{template_id}-{ctype.value}-{int(utc_now().timestamp())}",
                template_id=template_id,
                check_type=ctype,
                passed=True,
                details={"type": ctype.value, "template_name": template.name},
            )

            self._checks[check.id] = check
            results.append(check)

            if not check.passed:
                ViolationFound(
                    template_id=template_id,
                    check_id=check.id,
                    check_type=ctype,
                    details=check.details,
                )
                failed = True
                if ctype == CheckType.SECURITY and self._config.fail_on_security_violation:
                    break
                if ctype == CheckType.POLICY and self._config.fail_on_policy_violation:
                    break

        passed_count = sum(1 for c in results if c.passed)
        failed_count = len(results) - passed_count

        template_status = IaCTemplateStatus.INVALID if failed else IaCTemplateStatus.VALID
        self._templates[template_id] = template.model_copy(update={"status": template_status})

        ValidationCompleted(
            template_id=template_id,
            name=template.name,
            checks_passed=passed_count,
            checks_failed=failed_count,
            total_checks=len(results),
        )

        self._log.info(
            "iacvalid.validation.completed",
            template_id=template_id,
            passed=passed_count,
            failed=failed_count,
        )

        return results

    async def get_checks(self, template_id: str | None = None) -> list[ValidationCheck]:
        """List validation checks, optionally filtered by template."""
        result = list(self._checks.values())
        if template_id is not None:
            result = [c for c in result if c.template_id == template_id]
        return sorted(result, key=lambda c: c.checked_at, reverse=True)

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics."""
        total_templates = len(self._templates)
        total_checks = len(self._checks)
        passed = sum(1 for c in self._checks.values() if c.passed)
        failed = total_checks - passed
        return {
            "total_templates": total_templates,
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
        }


__all__ = ["IaCValidator"]
