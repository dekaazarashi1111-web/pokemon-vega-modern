#!/usr/bin/env python3
"""Stage72 Ability ROM runtime build/check entry point."""

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

from tools.modernization_p05_ability_rom_runtime import (  # noqa: E402
    DEFAULT_CONFIG,
    ModernizationP05AbilityRomRuntimeError,
    build_stage72_image,
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


def build_outputs(config_path: Path = DEFAULT_CONFIG) -> dict[str, bytes]:
    built = build_stage72_image(ROOT, config_path)
    outputs = built.config["outputs"]
    bps = create_bps(
        built.parent,
        built.rom,
        metadata=b"Stage71 to Stage72 Ability 312..317 CFRU-JP runtime adapters",
    )
    if apply_bps(built.parent, bps) != built.rom:
        raise ModernizationP05AbilityRomRuntimeError("Stage71→Stage72 BPS round-trip不一致")
    identity = {
        "path": outputs["incremental_bps"], "size": len(bps), "sha256": sha256(bps),
        "source_sha256": sha256(built.parent), "target_sha256": sha256(built.rom), "round_trip": True,
    }
    built.metadata["bps"] = identity
    built.checkpoint["bps"] = identity
    return {
        outputs["rom"]: built.rom,
        outputs["metadata"]: stable_json(built.metadata),
        outputs["allocation"]: built.allocation,
        outputs["incremental_bps"]: bps,
        outputs["checkpoint"]: stable_json(built.checkpoint),
        outputs["surface_matrix"]: stable_json(built.surface_matrix),
        outputs["payload"]: built.payload,
        outputs["symbols"]: stable_json(built.symbols),
        outputs["audit"]: stable_json(built.audit),
    }


def _compare(outputs: Mapping[str, bytes]) -> None:
    mismatches = [relative for relative, expected in outputs.items()
                  if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != expected]
    if mismatches:
        raise ModernizationP05AbilityRomRuntimeError(f"Stage72 published artifact不一致: {mismatches}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--check", action="store_true", help="書込みなしで全成果物をbyte比較")
    args = parser.parse_args(argv)
    outputs = build_outputs(args.config)
    if args.check:
        _compare(outputs)
    else:
        for relative, raw in outputs.items():
            _atomic_write(ROOT / relative, raw)
    print(f"Stage72 {'CHECK' if args.check else 'BUILD'} PASS artifacts={len(outputs)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ModernizationP05AbilityRomRuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
