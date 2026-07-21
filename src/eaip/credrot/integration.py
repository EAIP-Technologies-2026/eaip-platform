"""Credential rotator runtime module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from eaip.credrot.health import CredRotHealthCheck
from eaip.credrot.rotator import CredentialRotator

if TYPE_CHECKING:
    from eaip.runtime.kernel import RuntimeKernel


class CredRotRuntimeModule:
    name: str = "credrot"

    def __init__(self) -> None:
        self.rotator = CredentialRotator()
        self.health_check = CredRotHealthCheck(self.rotator)

    async def start(self, kernel: RuntimeKernel) -> None:
        kernel.register_module("credrot.rotator", self.rotator)

    async def stop(self, kernel: RuntimeKernel) -> None:
        pass
