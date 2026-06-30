"""Single source of truth for the EAIP package version.

This module is intentionally dependency-free so that build tooling, runtime
introspection, and packaging scripts can import it without side effects.
"""

from __future__ import annotations

from typing import Final

#: Public semantic version string (PEP 440 compliant).
__version__: Final[str] = "0.0.2"

#: Parsed ``(major, minor, patch)`` tuple. Pre-release / build metadata is
#: deliberately omitted; consult ``__version__`` for the canonical form.
__version_info__: Final[tuple[int, int, int]] = (0, 0, 2)

__all__ = ["__version__", "__version_info__"]
