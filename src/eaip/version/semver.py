"""A small, dependency-free SemVer 2.0.0 implementation.

Only the subset the Platform Foundation needs is supported: parsing,
comparison, and stringification. Pre-release & build metadata are preserved
but compared lexicographically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Self

_SEMVER_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    ^
    (?P<major>0|[1-9]\d*)
    \.
    (?P<minor>0|[1-9]\d*)
    \.
    (?P<patch>0|[1-9]\d*)
    (?:-(?P<prerelease>[0-9A-Za-z.-]+))?
    (?:\+(?P<build>[0-9A-Za-z.-]+))?
    $
    """,
    re.VERBOSE,
)


@dataclass(frozen=True, slots=True, order=False)
class Version:
    """Parsed SemVer 2.0.0 value object."""

    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    @classmethod
    def parse(cls, value: str) -> Self:
        """Parse a semantic version string."""
        match = _SEMVER_RE.match(value.strip())
        if not match:
            raise ValueError(f"invalid SemVer string {value!r}")
        gd = match.groupdict()
        return cls(
            major=int(gd["major"]),
            minor=int(gd["minor"]),
            patch=int(gd["patch"]),
            prerelease=gd["prerelease"] or "",
            build=gd["build"] or "",
        )

    def __str__(self) -> str:
        """Return the string representation of the semantic version."""
        core = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            core += f"-{self.prerelease}"
        if self.build:
            core += f"+{self.build}"
        return core

    # ------------------------------------------------------------------
    # Comparison — build metadata is ignored, pre-release lowers precedence.
    # ------------------------------------------------------------------
    def _key(self) -> tuple[int, int, int, int, str]:
        # A version *without* pre-release outranks one with pre-release.
        pre_rank = 0 if self.prerelease == "" else 1
        return (self.major, self.minor, self.patch, pre_rank, self.prerelease)

    def __lt__(self, other: Version) -> bool:
        """Compare if less than other."""
        if not isinstance(other, Version):  # pragma: no cover - defensive
            return NotImplemented
        a, b = self._key(), other._key()
        # Flip pre_rank: lower pre_rank = higher precedence.
        return (a[:3], -a[3], a[4]) < (b[:3], -b[3], b[4])

    def __le__(self, other: Version) -> bool:
        """Compare if less than or equal to other."""
        return self == other or self < other

    def __gt__(self, other: Version) -> bool:
        """Compare if greater than other."""
        return not self <= other

    def __ge__(self, other: Version) -> bool:
        """Compare if greater than or equal to other."""
        return not self < other

    def is_compatible_with(self, other: Version) -> bool:
        """Return ``True`` if ``other`` is API-compatible with ``self``.

        Per SemVer, two versions are compatible when their major versions
        match. (For 0.x, this method conservatively requires exact match of
        major+minor — see ``VERSIONING.md``.)
        """
        if self.major == 0 or other.major == 0:
            return self.major == other.major and self.minor == other.minor
        return self.major == other.major


__all__ = ["Version"]
