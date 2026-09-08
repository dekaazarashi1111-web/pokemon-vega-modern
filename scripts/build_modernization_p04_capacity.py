#!/usr/bin/env python3
"""工程4/5のID容量予約checkpointを生成または副作用なしで照合する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p04_capacity import (
    DEFAULT_OUTPUT,
    P04CapacityError,
    audit_p04_capacity_checkpoint,
    write_p04_capacity_checkpoint,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="ワークスペースroot")
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"task固有checkpoint path（既定: {DEFAULT_OUTPUT}）",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="checkpointを明示的に生成する")
    mode.add_argument("--check", action="store_true", help="副作用なしで照合する（既定）")
    parser.add_argument("--compact", action="store_true", help="結果JSONを1行で表示する")
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output
    if output.is_absolute():
        try:
            output = output.resolve().relative_to(root)
        except ValueError:
            print(
                json.dumps(
                    {"status": "FAIL", "error": "出力先はworkspace内に限定されます"},
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 1
    try:
        result = (
            write_p04_capacity_checkpoint(root, output_path=output)
            if args.write
            else audit_p04_capacity_checkpoint(root, output_path=output)
        )
    except (OSError, UnicodeError, json.JSONDecodeError, P04CapacityError) as exc:
        print(
            json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1
    options = {"ensure_ascii": False, "sort_keys": True}
    if args.compact:
        options["separators"] = (",", ":")
    else:
        options["indent"] = 2
    print(json.dumps(result, **options))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
