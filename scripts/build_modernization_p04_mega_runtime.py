#!/usr/bin/env python3
"""P04 Stage71 Mega runtime mapping/build入口。"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p04_mega_runtime import (  # noqa: E402
    DEFAULT_CONFIG,
    ModernizationP04MegaRuntimeError,
    build_mapping_contract,
    build_stage71_image,
    sha256,
    stable_json,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _read_config(config_path: Path) -> dict:
    path = config_path if config_path.is_absolute() else ROOT / config_path
    import json

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ModernizationP04MegaRuntimeError("Stage71 config rootがobjectではありません")
    return value


def build_outputs(config_path: Path = DEFAULT_CONFIG) -> dict[str, bytes]:
    built = build_stage71_image(ROOT, config_path)
    outputs = built.config["outputs"]
    bps = create_bps(
        built.parent,
        built.rom,
        metadata=b"Stage70 to Stage71 P04 49 Mega forward/reverse evolution rows",
    )
    if apply_bps(built.parent, bps) != built.rom:
        raise ModernizationP04MegaRuntimeError("Stage70→Stage71 BPS round-trip不一致")
    bps_identity = {
        "path": outputs["incremental_bps"],
        "size": len(bps),
        "sha256": sha256(bps),
        "source_sha256": sha256(built.parent),
        "target_sha256": sha256(built.rom),
        "round_trip": True,
    }
    built.metadata["bps"] = bps_identity
    built.checkpoint["bps"] = bps_identity
    mapping_raw = stable_json(built.mapping)
    metadata_raw = stable_json(built.metadata)
    checkpoint_raw = stable_json(built.checkpoint)
    index_raw = stable_json(built.generated_rows_index)
    return {
        outputs["rom"]: built.rom,
        outputs["metadata"]: metadata_raw,
        outputs["allocation"]: built.output_allocation,
        outputs["incremental_bps"]: bps,
        outputs["mapping"]: mapping_raw,
        outputs["checkpoint"]: checkpoint_raw,
        outputs["generated_rows"]: built.generated_rows,
        outputs["generated_rows_index"]: index_raw,
    }


def build_preflight_output(config_path: Path = DEFAULT_CONFIG) -> tuple[str, bytes]:
    config = _read_config(config_path)
    path = config["outputs"]["mapping"]
    return path, stable_json(build_mapping_contract(ROOT, config_path))


def _compare(outputs: Mapping[str, bytes]) -> None:
    mismatches: list[str] = []
    for relative, expected in outputs.items():
        path = ROOT / relative
        if not path.is_file() or path.read_bytes() != expected:
            mismatches.append(relative)
    if mismatches:
        raise ModernizationP04MegaRuntimeError(
            f"Stage71 published artifact不一致: {mismatches}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Stage70 identity前に固定mapping/capacity/source監査だけを書き出す",
    )
    parser.add_argument("--check", action="store_true", help="成果物を変更せずbyte比較する")
    args = parser.parse_args(argv)
    if args.preflight:
        relative, raw = build_preflight_output(args.config)
        outputs = {relative: raw}
    else:
        outputs = build_outputs(args.config)
    if args.check:
        _compare(outputs)
    else:
        for relative, raw in outputs.items():
            _atomic_write(ROOT / relative, raw)
    mode = "PREFLIGHT" if args.preflight else "ROM"
    verb = "CHECK" if args.check else "BUILD"
    print(f"Stage71 {mode} {verb} PASS artifacts={len(outputs)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ModernizationP04MegaRuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
