#!/usr/bin/env python3
"""Stage69 Floette Eternal gift builder入口。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_floette_gift import main


if __name__ == "__main__":
    raise SystemExit(main())
