#!/usr/bin/env python3
"""Render the palette category atlas via the U1 freeze runner."""
from __future__ import annotations

import subprocess
import sys


if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "tools/run_u1_freeze_roundtrip_overfit32.py", "--real-scenes", "1", "--overfit-scenes", "1"]))
