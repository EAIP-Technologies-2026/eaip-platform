"""Plugin contract, registry, loader, discovery, dependency validation, and lifecycle."""

from __future__ import annotations

from eaip.plugins.dependency import PluginDependencyValidator
from eaip.plugins.discovery import PluginDiscovery
from eaip.plugins.lifecycle import PluginLifecycleManager
from eaip.plugins.loader import PluginLoader
from eaip.plugins.plugin import Plugin, PluginDependency, PluginManifest
from eaip.plugins.registry import PluginRegistry

__all__ = [
    "Plugin",
    "PluginDependency",
    "PluginDependencyValidator",
    "PluginDiscovery",
    "PluginLifecycleManager",
    "PluginLoader",
    "PluginManifest",
    "PluginRegistry",
]
