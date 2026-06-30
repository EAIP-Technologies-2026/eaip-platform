"""Version utilities — SemVer parsing & comparison."""

from __future__ import annotations

from eaip.version.semver import Version

#: Re-export the package version for convenience.
from eaip._version import __version__ as PLATFORM_VERSION

__all__ = ["PLATFORM_VERSION", "Version"]
