"""EAIP application entry point.

Usage:
    python -m eaip
"""

from __future__ import annotations

import asyncio
import sys

from eaip._version import __version__
from eaip.app import ApplicationBuilder, run_application


def main() -> None:
    """Build and run the EAIP application with sensible defaults."""
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"eaip {__version__}")
        sys.exit(0)

    builder = ApplicationBuilder()
    asyncio.run(run_application(builder=builder))


if __name__ == "__main__":
    main()
