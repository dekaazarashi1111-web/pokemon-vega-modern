#!/usr/bin/env python3
"""工程6の未採用候補projectionを生成または副作用なしで監査する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p06_species import P06SpeciesError, audit_p06, render_review_projection


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="ワークスペースroot")
    parser.add_argument("--write", action="store_true", help="review projectionを明示的に再生成する")
    parser.add_argument("--no-archive-compare", action="store_true", help="固定ZIPとの再生成比較だけを省略する")
    parser.add_argument("--compact", action="store_true", help="JSONを1行で表示する")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.write:
            contract = json.loads(
                (root / "content/modernization/p06_species_adjustment_contract.json").read_text(encoding="utf-8")
            )
            projection = render_review_projection(root, contract)
            output = root / contract["review_partition"]["projection_path"]
            output.write_text(
                json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({"status": "WROTE", "path": str(output)}, ensure_ascii=False), file=sys.stderr)
        result = audit_p06(root, compare_archive=not args.no_archive_compare)
    except (OSError, UnicodeError, json.JSONDecodeError, P06SpeciesError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    if args.compact:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
