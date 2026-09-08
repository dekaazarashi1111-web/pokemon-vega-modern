#!/usr/bin/env python3
"""USER-MODERNIZATION-P01の読み取り専用exact-ROM容量監査を出力する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_capacity import (  # noqa: E402
    CapacityAuditError,
    build_modernization_capacity_audit,
    require_pass,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "active_play_baselineが固定するexact ROMの容量・consumer rootを"
            "変更なしで監査し、JSONを標準出力へ返す"
        )
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="FAIL reportでも非zero終了にしない（入力欠落・構文不正は常に非zero）",
    )
    parser.add_argument(
        "--compact", action="store_true", help="indentなしのcompact JSONを出力する"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_modernization_capacity_audit(args.root)
        if not args.no_check:
            require_pass(report)
    except CapacityAuditError as error:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "task": "USER-MODERNIZATION-P01",
                    "status": "FAIL",
                    "error": str(error),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            sort_keys=True,
            indent=None if args.compact else 2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
