#!/usr/bin/env python3
"""工程5の新Ability host runtime checkpointを生成または照合する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p05_ability_runtime import (  # noqa: E402
    DEFAULT_CONFIG,
    DEFAULT_OUTPUT,
    P05AbilityRuntimeError,
    audit_p05_ability_runtime_checkpoint,
    write_p05_ability_runtime_checkpoint,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="workspace root")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="checkpointを明示生成")
    mode.add_argument("--check", action="store_true", help="副作用なし照合（既定）")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    try:
        result = (
            write_p05_ability_runtime_checkpoint(
                args.root, config_path=args.config, output_path=args.output
            )
            if args.write
            else audit_p05_ability_runtime_checkpoint(
                args.root, config_path=args.config, output_path=args.output
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError, P05AbilityRuntimeError) as exc:
        print(
            json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1

    options: dict[str, object] = {"ensure_ascii": False, "sort_keys": True}
    if args.compact:
        options["separators"] = (",", ":")
    else:
        options["indent"] = 2
    print(json.dumps(result, **options))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
