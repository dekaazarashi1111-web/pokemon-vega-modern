#!/usr/bin/env python3
"""Modernization P03の訂正済みlearnset契約を決定的に生成・検査する。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_identity import stable_json  # noqa: E402
from tools.modernization_learnsets import (  # noqa: E402
    ModernizationLearnsetError,
    build_p03_artifacts,
)


DEFAULT_LEARNSETS = Path(
    "userfile/imports/modernization_p01/"
    "Pokemon_Vega_Stage61_技習得品質改善版_v1.3.0_20260905.zip"
)


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--learnsets-zip", type=Path, default=DEFAULT_LEARNSETS)
    parser.add_argument(
        "--check", action="store_true",
        help="書き込まず、3つのtracked契約とのbyte一致を検査する",
    )
    args = parser.parse_args(argv)
    action = "CHECK" if args.check else "BUILD"
    try:
        artifacts = build_p03_artifacts(ROOT, _absolute(args.learnsets_zip))
        for relative, document in artifacts.output_documents().items():
            output = ROOT / relative
            expected = stable_json(document)
            if args.check:
                if output.is_symlink() or not output.is_file():
                    raise ModernizationLearnsetError(
                        f"P03 tracked契約が通常ファイルではありません: {relative}"
                    )
                if output.read_bytes() != expected:
                    raise ModernizationLearnsetError(
                        f"P03 tracked契約が決定的生成結果と一致しません: {relative}"
                    )
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(expected)
    except (OSError, ModernizationLearnsetError) as error:
        print(f"MODERNIZATION_P03_{action}=FAIL", file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 1

    contract = artifacts.contract
    supply = contract["runtime_supply"]
    print(
        f"MODERNIZATION_P03_{action}=PASS "
        f"records={contract['corrected_adoption']['records']} "
        f"routes={contract['corrected_adoption']['routes']} "
        f"projected={supply['existing_slot_projection_rows']} "
        f"supply_required={supply['supply_required_rows']} "
        "move1063=RUNTIME_DEPENDENCY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
