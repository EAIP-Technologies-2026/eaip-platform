"""EAIP — Enterprise Autonomous Intelligence Platform.

This is the **Platform Foundation** package (delivered by EP-0002). It exposes
the reusable infrastructure on which every future EAIP capability is built:

* Application lifecycle, bootstrap & dependency injection.
* Typed configuration, settings hierarchy & feature flags.
* Structured logging, in-process events, health checks.
* Registries for services, capabilities & plugins.
* Stable shared types, protocols, interfaces & exception hierarchy.

The Foundation deliberately contains **no business logic**. Capability packs
(EP-0003+) import these primitives to implement domain features.

Example:
-------
>>> from eaip.application import build_platform
>>> platform = build_platform()
>>> platform.version
'0.0.2'
"""

from __future__ import annotations

from eaip._version import __version__, __version_info__

__all__ = ["__version__", "__version_info__"]
