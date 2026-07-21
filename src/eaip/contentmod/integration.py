"""Runtime module integration for the content moderation service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.contentmod.health import ContentModerationHealthCheck
from eaip.contentmod.models import ContentModerationConfig
from eaip.contentmod.moderator import ContentModerator
from eaip.logging.context import get_logger

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class ContentModerationRuntimeModule:
    name: str = "contentmod"

    def __init__(
        self,
        config: ContentModerationConfig | None = None,
        moderator: ContentModerator | None = None,
    ) -> None:
        self._config = config or ContentModerationConfig()
        self._moderator = moderator or ContentModerator()
        self._log = get_logger("eaip.contentmod.integration")

    @property
    def moderator(self) -> ContentModerator:
        return self._moderator

    async def start(self, kernel: RuntimeKernel) -> None:
        self._log.info("contentmod.module.starting")
        platform = kernel.platform
        capability = Capability(
            name="eaip.contentmod",
            title="Content Moderation Service",
            description="Review, filter, and flag user-generated content using moderation rules",
            version="0.1.0",
            status=CapabilityStatus.ENABLED,
            tags=("contentmod", "moderation", "filtering", "flagging"),
        )
        platform.capabilities.register(capability)
        platform.health.register(ContentModerationHealthCheck())
        self._log.info("contentmod.module.started")

    async def stop(self, kernel: RuntimeKernel) -> None:
        self._log.info("contentmod.module.stopping")


__all__ = ["ContentModerationRuntimeModule"]
