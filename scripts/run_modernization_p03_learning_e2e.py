#!/usr/bin/env python3
"""既採用P03経路を通常UIで習得・保存し、新規coreで確認する補助受入。"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "tools/mgba_modernization_p03_learning_e2e.c"
SCOPE = "P03_CATERPIE_LEVELUP_SAVE_RELOAD_REPRESENTATIVE"
ROM_SHA = "6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3"
SEED_SHA = "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"


def identity(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"通常fileが必要です: {path}")
    data = path.read_bytes()
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def validate_result(raw: bytes, mode: str, returncode: int) -> dict:
    if returncode != 0:
        raise ValueError(f"mGBA終了コード: {returncode}")
    result = json.loads(raw)
    if mode not in ("learn", "below-level"):
        raise ValueError("未知の試験mode")
    expected = {
        "schema_version": 1, "status": "PASS", "scope": SCOPE,
        "mode": mode, "rom_sha256": ROM_SHA, "species": 649,
        "initial_level": 8 if mode == "learn" else 7,
        "final_level": 9 if mode == "learn" else 8,
        "expected_move": 535 if mode == "learn" else 0,
        "normal_bag_party_input": True, "evolution_cancel_input": True,
        "normal_save_menu": True, "fresh_core_normal_continue": True,
        "representative_scheduler_e2e": True,
        "representative_save_reload_e2e": True,
        "breeding_e2e": False, "full_p03_acceptance": False,
        "release_ready": False, "warnings_errors": 0,
    }
    if not isinstance(result, dict) or set(result) != set(expected) | {"learned_slot_pp"}:
        raise ValueError("結果schemaが不一致")
    for key, value in expected.items():
        if type(result[key]) is not type(value) or result[key] != value:
            raise ValueError(f"結果契約が不一致: {key}")
    pp = result["learned_slot_pp"]
    if type(pp) is not int or not (0 <= pp <= 64) or ((pp > 0) != (mode == "learn")):
        raise ValueError("習得slot PPが不一致")
    return result


def run(output: Path) -> dict:
    output = output.absolute()
    if output.is_symlink():
        raise ValueError("symlink出力は禁止")
    output.resolve().relative_to((ROOT / ".local").resolve())
    output.mkdir(parents=True, exist_ok=True)
    # 再実行失敗を過去PASSで覆わない。原本は一切書き換えない。
    for name in ("result.json", "compile.stdout", "compile.stderr", "learn.stdout", "learn.stderr", "below-level.stdout", "below-level.stderr"):
        (output / name).unlink(missing_ok=True)
    cfg = json.loads((ROOT / "config/modernization_stage79_cumulative_mgba.json").read_text())
    rom = ROOT / cfg["runtime_candidate"]["rom"]["path"]
    domain = next(d for d in cfg["domains"] if d["id"] == "p02")
    seed = ROOT / domain["seed_save"]["path"]
    expected_rom = {"size": 33554432, "sha256": ROM_SHA}
    expected_seed = {"size": 131072, "sha256": SEED_SHA}
    if identity(rom) != expected_rom or identity(seed) != expected_seed:
        raise ValueError("固定ROM/seed identityが不一致")
    bindings = {}
    for row in [domain["runner"], *domain["dependencies"]]:
        actual = identity(ROOT / row["path"])
        if actual != {"size": row["size"], "sha256": row["sha256"]}:
            raise ValueError(f"既存依存sourceが不一致: {row['path']}")
        bindings[row["path"]] = actual
    target = json.loads((ROOT / "config/modernization_p03_stage65.json").read_text())["target"]
    route = next(r for r in target["level_up_routes"] if r["move_key"] == "MOVE_KEY_BUGBITE")
    if (target["species_id"], route["learning_level"], route["project_move_id"]) != (649, 9, 535):
        raise ValueError("既採用P03経路が変更されています")
    for name in (SOURCE, "scripts/run_modernization_p03_learning_e2e.py", "config/modernization_p03_stage65.json", "config/active_play_baseline.json"):
        bindings[name] = identity(ROOT / name)
    results = []
    with tempfile.TemporaryDirectory(prefix="p03-learning-", dir=ROOT / ".local") as temporary:
        work = Path(temporary)
        executable = work / "runner"
        command = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-Itools", SOURCE, "-lmgba", "-o", str(executable)]
        compilation = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
        (output / "compile.stdout").write_bytes(compilation.stdout)
        (output / "compile.stderr").write_bytes(compilation.stderr)
        if compilation.returncode:
            raise ValueError("strict C compile失敗")
        for mode in ("learn", "below-level"):
            private_rom, private_save = work / f"{mode}.gba", work / f"{mode}.srm"
            shutil.copyfile(rom, private_rom); private_rom.chmod(0o444)
            shutil.copyfile(seed, private_save)
            command = [str(executable), str(private_rom), str(private_save), ROM_SHA, SEED_SHA, "649", "9", "535", mode]
            try:
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=900)
            except subprocess.TimeoutExpired as error:
                (output / f"{mode}.stdout").write_bytes(error.stdout or b"")
                (output / f"{mode}.stderr").write_bytes(error.stderr or b"")
                raise
            finally:
                if identity(rom) != expected_rom or identity(private_rom) != expected_rom or identity(seed) != expected_seed:
                    raise ValueError("実行中にROM/seed原本が変更されました")
            (output / f"{mode}.stdout").write_bytes(completed.stdout)
            (output / f"{mode}.stderr").write_bytes(completed.stderr)
            result = validate_result(completed.stdout, mode, completed.returncode)
            if identity(private_save) == expected_seed:
                raise ValueError("保存fileがseedから変化していません")
            results.append({"mode": mode, "returncode": completed.returncode, "runner_result": result,
                            "stdout": identity(output / f"{mode}.stdout"), "stderr": identity(output / f"{mode}.stderr"),
                            "private_save_after": identity(private_save)})
    for name, before in bindings.items():
        if identity(ROOT / name) != before:
            raise ValueError(f"実行中にsource/baselineが変更されました: {name}")
    report = {"schema_version": 1, "status": "PASS", "scope": SCOPE,
              "source_bindings": bindings, "rom": expected_rom, "seed": expected_seed,
              "fresh_process_runs": 2, "cached_results_reused": 0, "cases": results,
              "full_p03_acceptance": False, "breeding_e2e": False, "release_ready": False,
              "active_baseline_changed": False}
    (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, default=ROOT / ".local/p03-learning-e2e")
    args = parser.parse_args()
    print(json.dumps(run(args.output_directory), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
