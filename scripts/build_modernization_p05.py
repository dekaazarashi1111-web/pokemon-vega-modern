#!/usr/bin/env python3
"""工程5のbattle content契約を生成・副作用なし検証する。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p05_contract import (  # noqa: E402
    ModernizationP05Error,
    build_p05_contract,
    stable_json,
)


OUTPUTS = {
    "content/modernization/p05_battle_content_contract.json": lambda contract: contract,
    "content/modernization/p05_runtime_handoff.json": lambda contract: {
        "schema_version": contract["schema_version"],
        "task": contract["task"],
        "status": contract["status"],
        "baseline": contract["baseline"],
        "new_move_requirements": contract["move_content"]["new_move_requirements"],
        "non_adopted_move_candidates": contract["move_content"][
            "non_adopted_move_candidates"
        ],
        "new_ability_requirements": contract["ability_content"]["new_ability_requirements"],
        "temporary_ability_assignments": [
            row
            for row in contract["ability_content"]["assignments"]
            if row["temporary_replaceable"]
        ],
        "non_adopted_p04_records": contract["ability_content"][
            "non_adopted_records"
        ],
        "save_compatibility": contract["save_compatibility"],
        "release_gates": contract["release_gates"],
    },
    "content/modernization/p05_data_only_patch_plan.json": lambda contract: {
        "schema_version": contract["schema_version"],
        "task": contract["task"],
        "status": "NO_CONFIRMED_DATA_ONLY_PATCH",
        "plan": contract["data_only_patch_plan"],
        "preserved_reference_differences": contract["move_content"][
            "preserved_reference_differences"
        ],
    },
}


def render_outputs(contract: dict[str, Any]) -> dict[str, bytes]:
    return {
        relative: stable_json(selector(contract))
        for relative, selector in OUTPUTS.items()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="再生成結果とtracked成果を比較する（書き込まない）",
    )
    args = parser.parse_args(argv)
    try:
        contract = build_p05_contract(ROOT)
        outputs = render_outputs(contract)
        if args.check:
            mismatches: list[str] = []
            for relative, expected in outputs.items():
                path = ROOT / relative
                if path.is_symlink() or not path.is_file():
                    mismatches.append(f"MISSING {relative}")
                elif path.read_bytes() != expected:
                    mismatches.append(f"DIFF {relative}")
            if mismatches:
                for mismatch in mismatches:
                    print(mismatch, file=sys.stderr)
                return 1
            print(
                "P05_CHECK=PASS "
                f"MOVE_NEW={contract['summary']['new_move_requirement_count']} "
                f"ABILITY_NEW={contract['summary']['new_ability_requirement_count']} "
                f"DATA_PATCH={contract['summary']['confirmed_data_only_patch_count']}"
            )
            return 0

        for relative, raw in outputs.items():
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            print(f"WROTE={relative} SIZE={len(raw)}")
        return 0
    except ModernizationP05Error as error:
        print(f"P05_ERROR={error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
