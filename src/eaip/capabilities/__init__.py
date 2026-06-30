"""Capability descriptors & registry — what the platform can *do*."""

from __future__ import annotations

from eaip.capabilities.capability import Capability, CapabilityStatus
from eaip.capabilities.registry import CapabilityRegistry

__all__ = ["Capability", "CapabilityRegistry", "CapabilityStatus"]
