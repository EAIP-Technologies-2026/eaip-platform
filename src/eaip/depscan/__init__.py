"""Dependency Scanner — EP-0151."""

from __future__ import annotations

from eaip.depscan.events import (
    ScanCompleted,
    ScanStarted,
    VulnerabilityFound,
)
from eaip.depscan.exceptions import (
    ScanError,
    TargetNotFoundError,
)
from eaip.depscan.health import DependencyScannerHealthCheck
from eaip.depscan.integration import DependencyScannerRuntimeModule
from eaip.depscan.models import (
    ScanConfig,
    ScanResult,
    ScanTarget,
    ScanTargetType,
    Severity,
    Vulnerability,
)
from eaip.depscan.scanner import DependencyScanner

__all__ = [
    "DependencyScanner",
    "DependencyScannerHealthCheck",
    "DependencyScannerRuntimeModule",
    "ScanCompleted",
    "ScanConfig",
    "ScanError",
    "ScanResult",
    "ScanStarted",
    "ScanTarget",
    "ScanTargetType",
    "Severity",
    "TargetNotFoundError",
    "Vulnerability",
    "VulnerabilityFound",
]
