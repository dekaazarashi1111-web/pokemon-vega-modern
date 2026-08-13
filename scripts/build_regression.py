#!/usr/bin/env python3
"""Build/check the T17 exact-ROM regression release candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.regression.model import RegressionError, build_outputs as build_model_outputs
from tools.regression.rom_runtime import (
    RuntimeBuildError,
    STAGE17,
    STAGE17_META,
    build_runtime_outputs,
)

QOL_FIXTURE = Path("tests/fixtures/qol_b.json")
MGBA_FIXTURE = Path("build/stages/17_mgba_smoke.json")


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _run(command: list[str], label: str) -> str:
    completed = subprocess.run(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RegressionError(f"{label} failed ({completed.returncode}): {detail[-2000:]}")
    return completed.stdout.strip()


def _qol_fixture(temp: Path) -> dict[str, object]:
    executable = temp / "qol-b-fixture"
    compiler = os.environ.get("CC", "cc")
    _run([
        compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
        "-Ioverlays/qol_b", "overlays/qol_b/qol_b.c",
        "tests/fixtures/qol_b_fixture.c", "-o", str(executable),
    ], "QOL-B host compile")
    result = json.loads(_run([str(executable)], "QOL-B host fixture"))
    if result.get("status") != "PASS":
        raise RegressionError("QOL-B host fixture did not report PASS")
    return result


def _mgba_fixture(temp: Path, stage: bytes, metadata: dict[str, object]) -> dict[str, object]:
    rom = temp / "17_regression.gba"
    executable = temp / "mgba-regression-smoke"
    rom.write_bytes(stage)
    compiler = os.environ.get("CC", "cc")
    _run([
        compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
        "tools/mgba_regression_smoke.c", "-o", str(executable), "-lmgba",
    ], "libmGBA smoke compile")
    symbols = metadata["symbols"]
    args = [
        str(executable), str(rom), hex(symbols["qol::QolB_RuntimeProbe"] | 1),
        hex(symbols["map_groups_root"]), hex(symbols["map_layouts_root"]),
        hex(symbols["wild_headers_root"]), str(metadata["payload"]["size"]),
        hex(symbols["script_portal_travel"]), hex(symbols["script_return_travel"]),
        hex(symbols["trainer_table"]), hex(symbols["progress::PewterCity_Gym"]),
        hex(symbols["progress::PokemonLeague_ChampionsRoom"]),
    ]
    first = json.loads(_run(args, "libmGBA exact-ROM smoke run 1"))
    second = json.loads(_run(args, "libmGBA exact-ROM smoke run 2"))
    if first != second or first.get("status") != "PASS":
        raise RegressionError("libmGBA smoke is not deterministic PASS")
    first["process_runs"] = 2
    first["rom_sha256"] = hashlib.sha256(stage).hexdigest()
    return first


def collect_outputs() -> dict[str, bytes]:
    runtime_outputs = build_runtime_outputs(ROOT)
    repeated = build_runtime_outputs(ROOT)
    if runtime_outputs != repeated:
        raise RegressionError("stage17 build is not byte-deterministic")
    stage = runtime_outputs[STAGE17.as_posix()]
    metadata = json.loads(runtime_outputs[STAGE17_META.as_posix()])
    with tempfile.TemporaryDirectory(prefix="vega-t17-") as temporary:
        temp = Path(temporary)
        qol = _qol_fixture(temp)
        mgba = _mgba_fixture(temp, stage, metadata)
    outputs = dict(runtime_outputs)
    outputs[QOL_FIXTURE.as_posix()] = _stable(qol)
    outputs[MGBA_FIXTURE.as_posix()] = _stable(mgba)
    outputs.update(build_model_outputs(ROOT, metadata, mgba, qol))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = collect_outputs()
        if args.mode == "build":
            for relative, raw in outputs.items():
                path = ROOT / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            print(f"T17 build: PASS ({len(outputs)} artifacts, exact-ROM smoke x2)")
        else:
            drift = [
                relative for relative, raw in outputs.items()
                if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != raw
            ]
            if drift:
                raise RegressionError("artifact drift: " + ", ".join(drift[:16]))
            print(f"T17 check: PASS ({len(outputs)} artifacts, side effects NONE)")
    except (RegressionError, RuntimeBuildError, OSError, ValueError, KeyError,
            subprocess.SubprocessError) as exc:
        print(f"T17 {args.mode}: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
