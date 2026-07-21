"""Hexagonal *ports* — abstract dependencies the platform needs from its host.

A port is what the platform *needs* (e.g. "give me current time"); an
adapter is *how* a particular implementation satisfies it (e.g.
``SystemClock``). Default adapters live in :mod:`eaip.infrastructure`.
"""

from __future__ import annotations

from eaip.ports.cache import CacheProvider
from eaip.ports.clock import ClockPort
from eaip.ports.id_generator import IdGeneratorPort
from eaip.ports.logger import LoggerPort
from eaip.ports.metrics import Counter, Gauge, Histogram, MetricsProvider, Timer
from eaip.ports.secret_provider import SecretProviderPort
from eaip.ports.tracing import Span, TracingProvider

__all__ = [
    "CacheProvider",
    "ClockPort",
    "Counter",
    "Gauge",
    "Histogram",
    "IdGeneratorPort",
    "LoggerPort",
    "MetricsProvider",
    "SecretProviderPort",
    "Span",
    "Timer",
    "TracingProvider",
]
