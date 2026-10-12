#!/usr/bin/env python3
"""工程4の外部素材を私用領域へ生成し、または副作用なしで照合する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p04_asset_importer import (
    DEFAULT_MANIFEST_RELATIVE,
    DEFAULT_OUTPUT_RELATIVE,
    P04AssetImportError,
    audit_p04_asset_import,
    generate_p04_asset_import,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="ワークスペースroot")
    parser.add_argument("--source-root", type=Path, help="commit固定済みsource checkout")
    parser.add_argument("--output-root", type=Path, help=f"Git外の生成先（既定: {DEFAULT_OUTPUT_RELATIVE}）")
    parser.add_argument("--manifest", type=Path, help=f"tracked manifest（既定: {DEFAULT_MANIFEST_RELATIVE}）")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="私用素材とmanifestを明示的に生成する")
    mode.add_argument("--check", action="store_true", help="既存成果を副作用なしで照合する（既定）")
    parser.add_argument("--compact", action="store_true", help="結果JSONを1行で出力する")
    args = parser.parse_args()

    root = args.root.resolve()
    source_root = args.source_root.resolve() if args.source_root else None
    output_root = args.output_root.resolve() if args.output_root else None
    manifest_path = args.manifest.resolve() if args.manifest else None
    try:
        if args.write:
            result = generate_p04_asset_import(
                root,
                source_root=source_root,
                output_root=output_root,
                manifest_path=manifest_path,
            )
        else:
            result = audit_p04_asset_import(
                root,
                source_root=source_root,
                output_root=output_root,
                manifest_path=manifest_path,
            )
    except (P04AssetImportError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    if args.compact:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
