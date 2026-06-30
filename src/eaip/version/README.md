# `eaip.version`

Single source of truth for SemVer parsing & comparison.

* `PLATFORM_VERSION` — current platform version string.
* `Version` — immutable value object with `parse`, comparison operators, and `is_compatible_with`.

The package deliberately implements only the SemVer subset the Foundation
needs. Capabilities requiring more elaborate version constraints should
depend on a library of their choice.
