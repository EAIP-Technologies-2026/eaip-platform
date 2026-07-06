"""Version utilities — SemVer parsing & comparison."""

from __future__ import annotations

#: Re-export the package version for convenience.
from eaip._version import __version__ as PLATFORM_VERSION
from eaip.version.semver import Version

__all__ = ["PLATFORM_VERSION", "Version"]
