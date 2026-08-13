#!/usr/bin/env python3
"""T13 クチバ早期アクセス縦切りをbuild/checkする。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.map_import import BuildError
from tools.map_import.vermilion_slice import build_outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = build_outputs(ROOT)
        if args.mode == "build":
            for relative, raw in outputs.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            print(f"T13 build: PASS ({len(outputs)} artifacts)")
        else:
            drift = [relative for relative, raw in outputs.items()
                     if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw]
            if drift:
                raise BuildError("artifact drift: " + ", ".join(drift))
            print(f"T13 check: PASS ({len(outputs)} artifacts, side effects NONE)")
    except (BuildError, OSError, ValueError, KeyError) as exc:
        print(f"T13 {args.mode}: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
