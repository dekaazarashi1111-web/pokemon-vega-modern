#!/usr/bin/env python3
"""Modernization P02の進化静的契約を決定的に生成・検査する。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_evolution import (  # noqa: E402
    ModernizationEvolutionError,
    ModernizationIdentityError,
    build_evolution_contract,
    stable_json,
)


DEFAULT_RESTORATION = Path(
    "userfile/imports/modernization_p01/"
    "Vega_Stage61_ID固定_原作復元監査資料.zip"
)
DEFAULT_OUTPUT = Path("content/modernization/p02_evolution_contract.json")


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restoration-zip", type=Path, default=DEFAULT_RESTORATION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き込まず、公開済み契約とのbyte一致だけを検査する",
    )
    args = parser.parse_args(argv)
    output = _absolute(args.output)
    action = "CHECK" if args.check else "BUILD"
    try:
        contract = build_evolution_contract(ROOT, _absolute(args.restoration_zip))
        expected = stable_json(contract)
        if args.check:
            if output.is_symlink() or not output.is_file():
                raise ModernizationEvolutionError(
                    f"P02進化契約が通常ファイルではありません: {args.output}"
                )
            if output.read_bytes() != expected:
                raise ModernizationEvolutionError(
                    "P02進化契約が入力・runtime・manifestからの決定的生成結果と一致しません"
                )
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(expected)
    except (OSError, ModernizationEvolutionError, ModernizationIdentityError) as error:
        print(f"MODERNIZATION_P02_{action}=FAIL", file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 1

    summary = contract["current_table"]["summary"]
    review = contract["review_only"]["summary"]
    print(
        f"MODERNIZATION_P02_{action}=PASS "
        f"rows={summary['rows']} "
        f"vega_unique={summary['adopted_vega_unique_rows']} "
        f"review_zip05={review['zip05_not_current']} "
        f"required_fixes={contract['findings']['required_fix_count']} "
        f"release_gate={contract['release_gate']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
