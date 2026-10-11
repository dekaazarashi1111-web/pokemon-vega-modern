#!/usr/bin/env python3
"""工程7の独自習得layer契約を生成・副作用なし検証する。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p07_learnsets import (  # noqa: E402
    ModernizationP07Error,
    build_p07_contract,
    stable_json,
)


OUTPUTS = {
    "content/modernization/p07_layered_learnset_contract.json": lambda contract: contract,
    "content/modernization/p07_runtime_handoff.json": lambda contract: {
        "schema_version": contract["schema_version"],
        "task": contract["task"],
        "status": contract["status"],
        "adopted_delta": contract["adopted_delta"],
        "precedence": contract["layer_model"]["precedence_low_to_high"],
        "conflict_rules": contract["layer_model"]["conflict_rules"],
        "preservation": contract["preservation"],
        "dependencies": contract["dependencies"],
        "runtime_handoff": contract["runtime_handoff"],
        "summary": contract["summary"],
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
        contract = build_p07_contract(ROOT)
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
                "P07_CHECK=PASS "
                f"NORMAL_TO_VEGA={contract['summary']['normal_species_to_vega_move_adopted']} "
                f"VEGA_TO_NORMAL={contract['summary']['vega_species_to_normal_move_adopted']} "
                f"DELETIONS={contract['summary']['explicit_deletions_adopted']} "
                "RUNTIME=BLOCKED"
            )
            return 0

        for relative, raw in outputs.items():
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            print(f"WROTE={relative} SIZE={len(raw)}")
        return 0
    except ModernizationP07Error as error:
        print(f"P07_ERROR={error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
