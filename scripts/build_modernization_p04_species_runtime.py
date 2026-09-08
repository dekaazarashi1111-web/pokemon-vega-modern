#!/usr/bin/env python3
"""Stage70 P04 species runtime生成入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p04_species_runtime import SpeciesRuntimeError, materialize  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="生成物を書かずbyte-exact再現性を検証")
    args = parser.parse_args()
    try:
        result = materialize(ROOT, check=args.check)
    except (OSError, ValueError, KeyError, SpeciesRuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
