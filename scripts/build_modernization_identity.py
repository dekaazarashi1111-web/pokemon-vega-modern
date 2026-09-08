#!/usr/bin/env python3
"""Modernization P01のcanonical identity契約を決定的に生成・検査する。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_identity import (  # noqa: E402
    ModernizationIdentityError,
    build_identity_contract,
    stable_json,
)


DEFAULT_LEARNSETS = Path(
    "userfile/imports/modernization_p01/"
    "Pokemon_Vega_Stage61_技習得品質改善版_v1.3.0_20260905.zip"
)
DEFAULT_RESTORATION = Path(
    "userfile/imports/modernization_p01/"
    "Vega_Stage61_ID固定_原作復元監査資料.zip"
)
DEFAULT_OUTPUT = Path("content/modernization/identity_contract.json")


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--learnsets-zip", type=Path, default=DEFAULT_LEARNSETS)
    parser.add_argument("--restoration-zip", type=Path, default=DEFAULT_RESTORATION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check", action="store_true",
        help="生成せず、公開済み契約とのbyte一致だけを検査する",
    )
    args = parser.parse_args(argv)
    output = _absolute(args.output)
    try:
        contract = build_identity_contract(
            ROOT, _absolute(args.learnsets_zip), _absolute(args.restoration_zip),
        )
        expected = stable_json(contract)
        if args.check:
            if output.is_symlink() or not output.is_file():
                raise ModernizationIdentityError(
                    f"identity契約が通常ファイルではありません: {args.output}"
                )
            actual = output.read_bytes()
            if actual != expected:
                raise ModernizationIdentityError(
                    "identity契約が入力・manifestからの決定的生成結果と一致しません"
                )
            action = "CHECK"
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(expected)
            action = "BUILD"
    except (OSError, ModernizationIdentityError) as error:
        print(f"MODERNIZATION_IDENTITY_{'CHECK' if args.check else 'BUILD'}=FAIL", file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 1

    summary = contract["target_normalization"]["summary"]
    print(
        f"MODERNIZATION_IDENTITY_{action}=PASS "
        f"species={summary['normalized_rows']} "
        f"apply={summary['normalized_apply_true']} "
        "caterpie=649:APPLY egg=412:EXCLUDED move1063=UNIMPLEMENTED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
