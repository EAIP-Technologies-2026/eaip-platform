"""PromptManager — render, validate, and manage prompt templates with versioning."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from eaip.context.events import PromptCreated, PromptVersioned
from eaip.context.exceptions import TemplatePolicyError, TemplateRenderError
from eaip.context.models import PromptTemplate, PromptVersion
from eaip.context.registry import PromptRegistry
from eaip.logging.context import get_logger

_VARIABLE_PATTERN: re.Pattern[str] = re.compile(r"\{(\w+)\}")


class PromptManager:
    """Manages prompt templates: render, validate, version, and policy checking.

    Wraps a PromptRegistry and adds template rendering with variable
    substitution, validation, and configurable policy checks.
    """

    def __init__(
        self,
        registry: PromptRegistry | None = None,
        *,
        event_publisher: Callable[[object], None] | None = None,
        policies: list[Callable[[PromptTemplate], None]] | None = None,
    ) -> None:
        """Initialize the PromptManager.

        Args:
            registry: Optional PromptRegistry instance. Creates one if not provided.
            event_publisher: Optional callable for publishing domain events.
            policies: Optional list of policy check callables. Each
                receives a PromptTemplate and may raise to reject it.
        """
        self._registry = registry or PromptRegistry()
        self._event_publisher = event_publisher or (lambda _: None)
        self._policies = list(policies or [])
        self._log = get_logger("eaip.context.templates")

    @property
    def registry(self) -> PromptRegistry:
        """Return the underlying PromptRegistry."""
        return self._registry

    # ------------------------------------------------------------------
    # Template lifecycle
    # ------------------------------------------------------------------

    def create_template(
        self,
        template_id: str,
        name: str,
        content: str,
        *,
        description: str = "",
        variables: tuple[str, ...] | None = None,
        version: str = "1.0.0",
        metadata: dict[str, Any] | None = None,
    ) -> PromptTemplate:
        """Create and register a new prompt template.

        Args:
            template_id: Unique identifier for the template.
            name: Human-readable name.
            content: Template content with ``{variable}`` placeholders.
            description: Optional description.
            variables: Optional explicit variable list. Auto-detected if empty.
            version: Initial version string.
            metadata: Optional metadata.

        Returns:
            The created PromptTemplate.

        Raises:
            TemplateRenderError: If template validation fails.
            TemplatePolicyError: If a policy check is violated.
        """
        detected = self._detect_variables(content)
        resolved_vars = tuple(variables) if variables else detected

        template = PromptTemplate(
            template_id=template_id,
            name=name,
            description=description,
            content=content,
            variables=resolved_vars,
            version=version,
            metadata=metadata or {},
        )

        self._validate_template(template)
        self._check_policies(template)

        self._registry.register(template)

        self._event_publisher(
            PromptCreated(
                prompt_id=template_id,
                name=name,
                version=version,
            )
        )
        self._log.info("template.created", template_id=template_id, version=version)
        return template

    def render(self, template_id: str, variables: Mapping[str, str]) -> str:
        """Render a prompt template with variable substitution.

        Args:
            template_id: The template identifier.
            variables: Mapping of variable names to values.

        Returns:
            The rendered template string.

        Raises:
            PromptNotFoundError: If the template is not found.
            TemplateRenderError: If rendering fails.
        """
        template = self._registry.get(template_id)

        missing = [v for v in template.variables if v not in variables]
        if missing:
            raise TemplateRenderError(
                f"Missing required variables: {', '.join(sorted(missing))}"
            )

        try:
            rendered = _VARIABLE_PATTERN.sub(
                lambda m: str(variables.get(m.group(1), m.group(0))),
                template.content,
            )
        except Exception as exc:
            raise TemplateRenderError(f"Failed to render template: {exc}") from exc

        self._log.debug("template.rendered", template_id=template_id)
        return rendered

    # ------------------------------------------------------------------
    # Version management
    # ------------------------------------------------------------------

    def create_version(
        self,
        template_id: str,
        content: str,
        version: str,
        *,
        change_log: str = "",
        author: str = "",
        set_current: bool = True,
    ) -> PromptVersion:
        """Create and register a new version of an existing template.

        Args:
            template_id: The template identifier.
            content: The version's content.
            version: The version string.
            change_log: Optional description of changes.
            author: Optional author identifier.
            set_current: Whether to make this the current version.

        Returns:
            The created PromptVersion.

        Raises:
            PromptNotFoundError: If the template is not found.
        """
        prompt_version = PromptVersion(
            version=version,
            content=content,
            change_log=change_log,
            author=author,
        )
        self._registry.add_version(template_id, prompt_version, set_current=set_current)

        self._event_publisher(
            PromptVersioned(
                prompt_id=template_id,
                version=version,
                author=author,
            )
        )
        self._log.info("template.versioned", template_id=template_id, version=version)
        return prompt_version

    def get_current_version(self, template_id: str) -> str:
        """Get the current version string for a template.

        Args:
            template_id: The template identifier.

        Returns:
            The current version string.
        """
        entry = self._registry.get_entry(template_id)
        return entry.current_version

    # ------------------------------------------------------------------
    # Validation & policies
    # ------------------------------------------------------------------

    def add_policy(self, policy: Callable[[PromptTemplate], None]) -> None:
        """Add a policy check function.

        Args:
            policy: A callable that receives a PromptTemplate and raises
                an exception to reject the template.
        """
        self._policies.append(policy)

    def _validate_template(self, template: PromptTemplate) -> None:
        """Validate that the template content is well-formed.

        Args:
            template: The template to validate.

        Raises:
            TemplateRenderError: If validation fails.
        """
        if not template.content.strip():
            raise TemplateRenderError("Template content must not be empty")

        declared = set(template.variables)
        detected = set(self._detect_variables(template.content))

        undeclared = detected - declared
        if undeclared:
            raise TemplateRenderError(
                f"Template contains undeclared variables: {', '.join(sorted(undeclared))}"
            )

        unmatched = declared - detected
        if unmatched:
            raise TemplateRenderError(
                f"Template declares unused variables: {', '.join(sorted(unmatched))}"
            )

    def _check_policies(self, template: PromptTemplate) -> None:
        """Run all registered policy checks against a template.

        Args:
            template: The template to check.

        Raises:
            TemplatePolicyError: If any policy check fails.
        """
        for policy in self._policies:
            try:
                policy(template)
            except TemplatePolicyError:
                raise
            except Exception as exc:
                raise TemplatePolicyError(f"Policy check failed: {exc}") from exc

    @staticmethod
    def _detect_variables(content: str) -> tuple[str, ...]:
        """Extract ``{variable}`` placeholders from template content.

        Args:
            content: The template content.

        Returns:
            A tuple of detected variable names in order of appearance.
        """
        return tuple(dict.fromkeys(m.group(1) for m in _VARIABLE_PATTERN.finditer(content)))


__all__ = ["PromptManager"]
