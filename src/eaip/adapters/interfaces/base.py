"""Base class for adapters bridging EAIP and external systems.

This is **not** a place for vendor SDKs. Capability packs (EP-0003+) provide
concrete subclasses for their domains (LLM adapters, tool adapters, memory
adapters, ...).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from eaip.metadata.component import ComponentMetadata


class AdapterCapability(BaseModel):
    """A coarse-grained label describing what an adapter can do.

    Capability packs subclass this with stricter, domain-specific fields.
    """

    name: str
    description: str = ""


class AbstractAdapter(ABC):
    """Common base for any adapter to an external system."""

    @property
    @abstractmethod
    def metadata(self) -> ComponentMetadata:
        """Return self-describing metadata for this adapter."""

    @property
    @abstractmethod
    def capabilities(self) -> tuple[AdapterCapability, ...]:
        """Return the capability labels this adapter offers."""

    @abstractmethod
    async def health(self) -> bool:
        """Lightweight self-check; ``True`` if the adapter is usable."""


__all__ = ["AbstractAdapter", "AdapterCapability"]
