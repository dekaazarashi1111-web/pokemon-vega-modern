#!/usr/bin/env python3
"""T16 dual-region content population build/check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.content.populate_content import PopulationError, build_outputs


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
            print(f"T16 build: PASS ({len(outputs)} artifacts)")
        else:
            drift = [
                relative
                for relative, raw in outputs.items()
                if not (ROOT / relative).is_file()
                or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                raise PopulationError("artifact drift: " + ", ".join(drift[:12]))
            print(f"T16 check: PASS ({len(outputs)} artifacts, side effects NONE)")
    except (PopulationError, OSError, ValueError, KeyError) as exc:
        print(f"T16 {args.mode}: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
