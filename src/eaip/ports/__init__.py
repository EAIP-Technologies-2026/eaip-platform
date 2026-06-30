"""Hexagonal *ports* — abstract dependencies the platform needs from its host.

A port is what the platform *needs* (e.g. "give me current time"); an
adapter is *how* a particular implementation satisfies it (e.g.
``SystemClock``). Default adapters live in :mod:`eaip.infrastructure`.
"""

from __future__ import annotations

from eaip.ports.clock import ClockPort
from eaip.ports.id_generator import IdGeneratorPort
from eaip.ports.secret_provider import SecretProviderPort

__all__ = ["ClockPort", "IdGeneratorPort", "SecretProviderPort"]
