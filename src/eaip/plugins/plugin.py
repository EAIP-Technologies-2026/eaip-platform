"""Plugin contract — what a third-party module must implement to extend EAIP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from eaip.metadata.component import ComponentKind, ComponentMetadata
from eaip.types import NonEmptyStr

if TYPE_CHECKING:  # pragma: no cover
    from eaip.platform.platform import Platform


class PluginDependency(BaseModel):
    """Declares a dependency on another plugin.

    Attributes:
        name: The plugin name this dependency targets.
        version_spec: Semver range spec (``>=1.0.0,<2.0.0``, ``~1.2.0``,
            ``^1.2.3``, ``*``). An empty string matches any version.
        optional: If True, a missing or mismatched dependency is a
            warning, not an error.
    """

    name: NonEmptyStr = Field(description="The plugin name this dependency targets.")
    version_spec: str = Field(
        default="*",
        description="Semver range spec (empty or '*' = any version).",
    )
    optional: bool = Field(default=False, description="If True, failure is a warning.")


class PluginManifest(BaseModel):
    """Static declaration of a plugin's identity and contract version.

    A manifest is read **before** the plugin is loaded so the registry can
    detect duplicates and incompatible contract versions without importing
    user code.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: NonEmptyStr = Field(description="Globally unique plugin name.")
    version: NonEmptyStr = Field(description="Plugin's semantic version.")
    contract_version: NonEmptyStr = Field(
        default="1.0.0",
        description="The plugin contract version this plugin targets.",
    )
    description: str = Field(default="")
    provides_capabilities: tuple[str, ...] = Field(default=())
    entry_point: str = Field(
        default="",
        description="Dotted module path to the plugin's entry point class.",
    )
    requires_platform: str = Field(
        default=">=0.1.0",
        description="Semver range spec for the EAIP platform version.",
    )
    tags: tuple[str, ...] = Field(default=())
    dependencies: tuple[PluginDependency, ...] = Field(
        default=(),
        description="Plugins this plugin depends on.",
    )

    def to_metadata(self) -> ComponentMetadata:
        """Converts the manifest into component metadata.

        Returns:
            The component metadata representing this plugin.
        """
        return ComponentMetadata(
            name=self.name,
            kind=ComponentKind.PLUGIN,
            version=self.version,
            description=self.description,
            tags=self.tags or self.provides_capabilities,
        )


@runtime_checkable
class Plugin(Protocol):
    """Structural contract every plugin must satisfy.

    * ``manifest`` — static identity.
    * ``activate(platform)`` — register capabilities, services, hooks. Must
      be idempotent: calling it twice on the same platform is a contract
      violation but must not corrupt state.
    * ``deactivate(platform)`` — remove everything ``activate`` added.
    """

    manifest: PluginManifest

    async def activate(self, platform: Platform) -> None:
        """Activates the plugin.

        Args:
            platform: The platform instance to activate the plugin on.
        """
        ...

    async def deactivate(self, platform: Platform) -> None:
        """Deactivates the plugin.

        Args:
            platform: The platform instance to deactivate the plugin on.
        """
        ...


__all__ = ["Plugin", "PluginManifest"]
