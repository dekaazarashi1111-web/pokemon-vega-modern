#!/usr/bin/env python3
"""clean FireRedからStage58のchain/direct/source再構築を照合する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_stage58_qol_world_convenience_debug import (  # noqa: E402
    DEFAULT_CONFIG,
    STAGE,
    TASK,
    _build_static,
    _read_config,
)
from tools.release.bps import apply_bps  # noqa: E402


STAGE57_CLEAN_PATCH = Path(
    "build/patches/firered-jpn-rev0-to-comprehensive-debug-repair-stage57.bps"
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n").encode("utf-8")


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--require-mgba", action="store_true",
        help="source rebuildにもfull mGBA確定metadataを要求する",
    )
    args = parser.parse_args()
    try:
        config = _read_config(args.config)
        outputs = config["outputs"]
        clean = (ROOT / config["inputs"]["clean_rom"]["path"]).read_bytes()
        expected57 = (ROOT / config["inputs"]["stage57_rom"]["path"]).read_bytes()
        expected58 = (ROOT / outputs["rom"]).read_bytes()
        patch57 = (ROOT / STAGE57_CLEAN_PATCH).read_bytes()
        incremental = (ROOT / outputs["incremental_bps"]).read_bytes()
        direct = (ROOT / outputs["clean_bps"]).read_bytes()
        rebuilt57 = apply_bps(clean, patch57)
        chained = apply_bps(rebuilt57, incremental)
        direct_output = apply_bps(clean, direct)
        first, second = _build_static(args.config), _build_static(args.config)
        source_output = first[outputs["rom"]]
        source_metadata = json.loads(first[outputs["metadata"]])
        if first != second:
            raise ValueError("source buildがbyte deterministicではありません")
        if args.require_mgba and source_metadata.get("status") != "PASS":
            raise ValueError("Stage58 full mGBA証跡が未確定です")
        if rebuilt57 != expected57:
            raise ValueError("clean→Stage57 chain不一致")
        if not (chained == direct_output == source_output == expected58):
            raise ValueError("Stage58 chain/direct/source identity不一致")
        report = {
            "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
            "clean": {"size": len(clean), "sha256": _sha(clean)},
            "stage57": {"size": len(rebuilt57), "sha256": _sha(rebuilt57)},
            "stage58": {"size": len(expected58), "sha256": _sha(expected58)},
            "patches": {
                "clean_to_stage57": {"path": str(STAGE57_CLEAN_PATCH),
                                     "sha256": _sha(patch57)},
                "stage57_to_stage58": {"path": outputs["incremental_bps"],
                                      "sha256": _sha(incremental)},
                "clean_to_stage58": {"path": outputs["clean_bps"],
                                    "sha256": _sha(direct)},
            },
            "checks": {"clean_to_stage57": True, "incremental_chain": True,
                       "direct_clean": True, "source_rebuild_twice": True,
                       "all_outputs_identical": True},
        }
        rendered = _stable(report)
        path = ROOT / outputs["clean_rebuild"]
        if args.mode == "build":
            _write(path, rendered)
        elif not path.is_file() or path.read_bytes() != rendered:
            raise ValueError("Stage58 clean rebuild report drift")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"Stage58 clean rebuild {args.mode} failed: {error}", file=sys.stderr)
        return 1
    print(f"Stage58 clean rebuild {args.mode}: PASS sha256={report['stage58']['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
