#!/usr/bin/env python3
"""Stage68 Mega Stone BP shop builder入口。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_mega_shop import main


if __name__ == "__main__":
    raise SystemExit(main())
