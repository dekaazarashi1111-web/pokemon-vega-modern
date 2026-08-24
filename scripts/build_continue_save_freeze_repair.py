#!/usr/bin/env python3
"""Stage50のContinue描画・1歩後停止を修正しStage51を生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.continue_save_freeze_repair import (  # noqa: E402
    GBA_ROM_BASE,
    repair_stage50_rom,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402


TASK = "USER-20260824-STAGE50-CONTINUE-SAVE-FREEZE-REPAIR"
STAGE = 51
ROM_SIZE = 32 * 1024 * 1024
STAGE50_SHA256 = "af9bd50194e16fc409a31b6c179ec8c53a15d6961220daf29a0bd38a2b7dc92d"
CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"

STAGE50_ROM = Path("build/stages/50_interaction_ownership_repair.gba")
STAGE50_META = Path("build/stages/50_interaction_ownership_repair.json")
STAGE50_ALLOCATION = Path("build/stages/50_allocation.json")
STAGE50_CLEAN_BPS = Path("build/patches/clean-to-interaction-owner-stage50.bps")
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
STAGE17_META = Path("build/stages/17_regression.json")
TRAINER_META = Path("build/stages/35_trainer_changekit_final.json")

OUTPUTS = {
    "rom": Path("build/stages/51_continue_save_freeze_repair.gba"),
    "metadata": Path("build/stages/51_continue_save_freeze_repair.json"),
    "allocation": Path("build/stages/51_allocation.json"),
    "mgba": Path("build/stages/51_mgba_continue_field.json"),
    "incremental_bps": Path("build/patches/stage50-to-continue-save-freeze-stage51.bps"),
    "clean_bps": Path("build/patches/clean-to-continue-save-freeze-stage51.bps"),
    "report_json": Path("reports/generated/continue_save_freeze_repair.json"),
    "report_md": Path("reports/generated/continue_save_freeze_repair.md"),
}


class ContinueSaveFreezeBuildError(RuntimeError):
    """Stage51の入力、修正、mGBA検証、または生成物が不一致。"""


def _fail(message: str) -> NoReturn:
    raise ContinueSaveFreezeBuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _read(path: Path, *, digest: str | None = None,
          size: int | None = None) -> bytes:
    raw = (ROOT / path).read_bytes()
    if digest is not None and _sha(raw) != digest:
        _fail(f"入力hash不一致: {path}")
    if size is not None and len(raw) != size:
        _fail(f"入力size不一致: {path}")
    return raw


def _json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _compile(source: Path, output: Path) -> None:
    completed = subprocess.run([
        os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra",
        "-Werror", "-pedantic", str(ROOT / source), "-o", str(output),
        "-lmgba",
    ], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        _fail(f"mGBA compile failed ({source}): " + completed.stderr.strip()[-3000:])


def _run_json(arguments: list[str], label: str) -> dict[str, Any]:
    completed = subprocess.run(arguments, cwd=ROOT, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        _fail(f"{label} failed: " + detail[-4000:])
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        _fail(f"{label} JSON invalid: {error}")
    if not isinstance(value, dict) or value.get("status") != "PASS":
        _fail(f"{label} status differs")
    return value


def _interaction_smoke(rom: bytes, metadata: Mapping[str, Any]) -> dict[str, Any]:
    stage17 = _json(STAGE17_META)
    trainer = _json(TRAINER_META)
    plan = metadata["interaction_plan"]
    payload = metadata["payload"]
    address = lambda label: (GBA_ROM_BASE + int(payload["offset"])
                             + int(plan["labels"][label]))
    shinichi = int(metadata["trainer_audit"]["shinichi"]["command_address"])
    with tempfile.TemporaryDirectory(prefix="vega-stage51-interaction-") as raw:
        directory = Path(raw)
        rom_path = directory / OUTPUTS["rom"].name
        executable = directory / "mgba-interaction-ownership"
        rom_path.write_bytes(rom)
        _compile(Path("tools/mgba_interaction_ownership_smoke.c"), executable)
        arguments = [
            str(executable), str(rom_path),
            hex(int(stage17["symbols"]["map_groups_root"])),
            hex(GBA_ROM_BASE + int(payload["offset"])),
            hex(GBA_ROM_BASE + int(payload["offset"]) + int(payload["size"])),
            hex(address("script_hisui")),
            hex(address("runtime_moving_wild_encounter") | 1),
            hex(int(trainer["trainer_table"]["new_address"])),
            hex(shinichi), "armv4t-tail",
        ]
        runs = [_run_json(arguments, "Stage51 interaction smoke") for _ in range(2)]
    if runs[0] != runs[1]:
        _fail("Stage51 interaction smoke stdoutが非決定的です")
    return runs[0] | {"process_runs": 2, "stdout_identical": True}


def _continue_smoke(rom: bytes) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="vega-stage51-continue-") as raw:
        directory = Path(raw)
        rom_path = directory / OUTPUTS["rom"].name
        save_path = directory / "stage51-natural-codex.srm"
        image_prefix = directory / "stage51-natural-codex"
        bootstrap = directory / "mgba-codex-bootstrap"
        probe = directory / "mgba-continue-field"
        rom_path.write_bytes(rom)
        _compile(Path("tools/mgba_codex_battle_ipad_bootstrap.c"), bootstrap)
        _compile(Path("tools/mgba_continue_field_smoke.c"), probe)
        generated = _run_json(
            [str(bootstrap), str(rom_path), str(save_path)],
            "Stage51 natural save bootstrap",
        )
        save_raw = save_path.read_bytes()
        if len(save_raw) != 0x20000:
            _fail("Stage51 natural save size differs")
        arguments = [str(probe), str(rom_path), str(save_path), str(image_prefix)]
        runs = [_run_json(arguments, "Stage51 natural Continue") for _ in range(2)]
        if runs[0] != runs[1]:
            _fail("Stage51 natural Continue stdoutが非決定的です")
        if runs[0].get("warnings") != 0 or int(runs[0].get("stable_two_step_paths", 0)) < 1:
            _fail("Stage51 natural Continueの移動またはwarningが不正です")
        directions = runs[0].get("directions", [])
        if not isinstance(directions, list) or not directions:
            _fail("Stage51 natural Continue direction evidenceがありません")
        for direction in directions:
            initial = direction.get("initial", {})
            if initial.get("callback") != "08055e75" or initial.get("script") != 0 \
                    or initial.get("map") != "96/5" \
                    or (initial.get("x"), initial.get("y")) != (20, 20) \
                    or int(initial.get("map_view_distinct", 0)) < 8:
                _fail("Stage51 Continue initial field state differs")
        ppm = Path(str(image_prefix) + ".ppm")
        if not ppm.is_file() or ppm.stat().st_size <= 1024:
            _fail("Stage51 Continue framebuffer evidence is missing")
    return {
        "status": "PASS",
        "bootstrap": generated,
        "continue": runs[0],
        "process_runs": 2,
        "stdout_identical": True,
        "generated_save_size": len(save_raw),
        "generated_save_sha256": _sha(save_raw),
        "natural_continue": True,
        "field_framebuffer_written_in_temp": True,
        "artifacts_written": [],
    }


def _markdown(report: Mapping[str, Any]) -> bytes:
    return (f"""# Stage51 Continue / save freeze repair

- Status: **{report['status']}**
- Input Stage50: `{report['input']['sha256']}`
- Output Stage51: `{report['output']['sha256']}`

## 原因と修正

- Stage50の移動時遭遇wrapperがARM7TDMIに存在しないThumb `BLX register`（`0x4798`）を実行していた。
- wrapperをARMv4T互換tail-callへ置換し、移動中は元の遭遇処理、方向転換中はfalseを返す。
- ROM変更は既存wrapper {report['repair']['wrapper_size']} byte内の{report['repair']['changed_bytes']} byteだけで、宣言外変更0。
- Stage47由来の試験用saveは保存map viewが破損していたため、通常new game→stock warp/load→SaveMapView→2世代saveで再発行する。

## 回帰

- 自然Continue: map `96/5`、座標`20/20`、overworld callback、script context無効を確認。
- 実入力2歩: stable path {report['mgba']['continue']['stable_two_step_paths']}、mGBA warning/error 0。
- Stage50 interaction / trainer / 511番水道 / encounter grace / Dark Pulse / Focus Sash: PASS x2。
- clean→Stage50復元、Stage50差分BPS、clean直接BPS: byte一致。
""").encode("utf-8")


def _build_outputs() -> dict[Path, bytes]:
    stage50 = _read(STAGE50_ROM, digest=STAGE50_SHA256, size=ROM_SIZE)
    clean = _read(CLEAN_ROM, digest=CLEAN_SHA256, size=ROM_SIZE // 2)
    metadata50 = _json(STAGE50_META)
    reconstructed = apply_bps(clean, _read(STAGE50_CLEAN_BPS))
    if reconstructed != stage50:
        _fail("clean→Stage50 pinned reconstruction differs")
    output, repair = repair_stage50_rom(stage50, metadata50)
    interaction = _interaction_smoke(output, metadata50)
    continue_result = _continue_smoke(output)
    incremental = create_bps(stage50, output,
                             metadata=b"Stage50 to Stage51 Continue save freeze repair")
    direct = create_bps(clean, output,
                        metadata=b"Clean FireRed JPN Rev0 to Stage51 Continue save freeze repair")
    if apply_bps(stage50, incremental) != output or apply_bps(clean, direct) != output:
        _fail("Stage51 BPS round-trip differs")
    report = {
        "schema_version": 1, "task": TASK, "stage": STAGE, "status": "PASS",
        "input": {"path": str(STAGE50_ROM), "size": len(stage50),
                  "sha256": _sha(stage50)},
        "output": {"path": str(OUTPUTS["rom"]), "size": len(output),
                   "sha256": _sha(output)},
        "repair": repair,
        "mgba": {"interaction": interaction, **continue_result},
        "reconstruction": {"clean_to_stage50": True, "stage50_hash_pinned": True},
        "bps": {
            "incremental": {"path": str(OUTPUTS["incremental_bps"]),
                            "size": len(incremental), "sha256": _sha(incremental),
                            "round_trip": True},
            "clean": {"path": str(OUTPUTS["clean_bps"]),
                      "size": len(direct), "sha256": _sha(direct),
                      "round_trip": True},
        },
        "invariants": {
            "save_abi_unchanged": True, "map_graph_unchanged": True,
            "trainer_data_unchanged": True, "allocation_unchanged": True,
            "outside_wrapper_changes_zero": True, "armv4t_only": True,
        },
    }
    return {
        OUTPUTS["rom"]: output,
        OUTPUTS["metadata"]: _stable(report),
        OUTPUTS["allocation"]: _read(STAGE50_ALLOCATION),
        OUTPUTS["mgba"]: _stable(report["mgba"]),
        OUTPUTS["incremental_bps"]: incremental,
        OUTPUTS["clean_bps"]: direct,
        OUTPUTS["report_json"]: _stable(report),
        OUTPUTS["report_md"]: _markdown(report),
    }


def _write(outputs: Mapping[Path, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check(outputs: Mapping[Path, bytes]) -> None:
    drift = [str(path) for path, raw in outputs.items()
             if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != raw]
    if drift:
        _fail("Stage51 generated output drift: " + ", ".join(drift))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    args = parser.parse_args()
    try:
        outputs = _build_outputs()
        _write(outputs) if args.mode == "build" else _check(outputs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            ContinueSaveFreezeBuildError) as error:
        print(f"Stage51 Continue/save freeze repair failed: {error}", file=sys.stderr)
        return 1
    report = json.loads(outputs[OUTPUTS["metadata"]])
    print(json.dumps({
        "status": report["status"], "stage": STAGE,
        "rom_sha256": report["output"]["sha256"],
        "changed_bytes": report["repair"]["changed_bytes"],
        "stable_two_step_paths": report["mgba"]["continue"]["stable_two_step_paths"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
