#!/usr/bin/env python3
"""工程8の統合matrix/runtime/release handoffを生成または検証する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p08_integration import (  # noqa: E402
    ModernizationP08Error,
    build_integration_matrix,
    build_release_handoff,
    build_runtime_handoff,
    stable_json,
)
from tools.modernization_p08_stage79_evidence import (  # noqa: E402
    EvidenceError,
    attach_outputs,
)


from tools.modernization_p08_representative_evidence import attach_outputs as attach_representative  # noqa: E402

from tools.modernization_p08_stage81_evidence import attach_outputs as attach_native  # noqa: E402

OUTPUTS = {
    "content/modernization/p08_integration_matrix.json": lambda matrix: matrix,
    "content/modernization/p08_runtime_handoff.json": build_runtime_handoff,
    "content/modernization/p08_release_handoff.json": build_release_handoff,
}


def render_outputs(matrix: dict[str, Any]) -> dict[str, bytes]:
    historical = {
        relative: stable_json(builder(matrix))
        for relative, builder in OUTPUTS.items()
    }
    return attach_native(attach_representative(attach_outputs(historical, ROOT), ROOT), ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="固定入力から再生成し、既存成果とbyte比較する（書込なし）",
    )
    args = parser.parse_args(argv)
    try:
        matrix = build_integration_matrix(ROOT)
        outputs = render_outputs(matrix)
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
            document = json.loads(outputs['content/modernization/p08_integration_matrix.json'])
            current = document.get('current_native_pp_acceptance') or document.get('current_cumulative_runtime')
            print(
                "P08_CHECK=PASS STATUS=CHECKPOINT_NOT_RELEASE_CANDIDATE "
                f"INPUTS={matrix['snapshot']['tracked_input_count']} "
                f"COMPLETED={matrix['integration_summary']['completed_phase_count']} "
                "ACTIVE_STAGE=62 "
                "HISTORICAL_CANDIDATE_STAGE="
                f"{matrix['integration_summary']['highest_pinned_candidate_stage']} "
                f"CUMULATIVE_RUNTIME_STAGE={current['candidate_stage'] if current else 'NOT_ADOPTED'} "
                f"CUMULATIVE_DOMAINS={current['domain_count'] if current else 0} "
                "RELEASE_READY=false"
            )
            return 0

        for relative, raw in outputs.items():
            path = ROOT / relative
            if path.is_symlink():
                raise ModernizationP08Error(f"出力先がsymlinkです: {relative}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            print(f"WROTE={relative} SIZE={len(raw)}")
        return 0
    except (ModernizationP08Error, EvidenceError, OSError, ValueError) as error:
        print(f"P08_ERROR={error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
