"""Plugin contract — what a third-party module must implement to extend EAIP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from eaip.metadata.component import ComponentKind, ComponentMetadata
from eaip.types import NonEmptyStr

if TYPE_CHECKING:  # pragma: no cover
    from eaip.platform.platform import Platform


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

    def to_metadata(self) -> ComponentMetadata:
        return ComponentMetadata(
            name=self.name,
            kind=ComponentKind.PLUGIN,
            version=self.version,
            description=self.description,
            tags=self.provides_capabilities,
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

    async def activate(self, platform: Platform) -> None: ...

    async def deactivate(self, platform: Platform) -> None: ...


__all__ = ["Plugin", "PluginManifest"]
