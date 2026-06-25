#!/usr/bin/env python
"""CLI entry for the LoReflection native 3D-FRONT prototype builder.

The implementation lives in ``loreflection.builders.scene_package_builder``.
This script intentionally remains a thin command-line wrapper so the real
preprocessing pipeline is owned by the LoReflection package rather than by a
one-off tool script.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from loreflection.builders.scene_package_builder import main


if __name__ == "__main__":
    raise SystemExit(main())
