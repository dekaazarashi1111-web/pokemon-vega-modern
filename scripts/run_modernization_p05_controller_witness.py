#!/usr/bin/env python3
"""Stage80のP05代表4ケースを新規processで実行する。全P05受入ではない。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCOPE = "P05_DRAGONIZE_CONTROLLER_TURN_REPRESENTATIVE"
ROM_ID = {"size": 33554432, "sha256": "6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3"}
BASELINE_ID = {"size": 394, "sha256": "4800257add049ea99cdedda91413a70a255dcff9a85823463596edefa8785053"}
CASES: dict[str, tuple[int, int, bool]] = {
    "dragonize_ghost": (312, 7, True),
    "no_ability_ghost": (0, 7, False),
    "no_ability_normal": (0, 0, True),
    "dragonize_normal": (312, 0, True),
}
SOURCE = "tools/mgba_modernization_p05_controller_witness.c"
HEADER = "tools/modernization_p05_turn_observer.h"
SCRIPT = "scripts/run_modernization_p05_controller_witness.py"
CONFIG = "config/modernization_stage79_cumulative_mgba.json"
BASELINE = "config/active_play_baseline.json"
DEPENDENCIES = {
    "tools/mgba_battle_core_smoke.c": {"size": 94688, "sha256": "ed9875695ca60c61960685ac2f8e810a183c8eedd703e56545d67bde3df5cf24"},
    "tools/mgba_ai_fixture_runner.c": {"size": 36272, "sha256": "f03c4a894d1b76234f6e0f39c2bcb6400c416977d6e27265024abe16d248fd8f"},
}
LOG_NAMES = ("compile", *CASES)


def identity(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"通常fileが必要です: {path}")
    data = path.read_bytes()
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def strict_json(raw: bytes) -> Any:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in rows:
            if key in out:
                raise ValueError(f"重複JSON key: {key}")
            out[key] = value
        return out

    def constant(value: str) -> None:
        raise ValueError(f"非有限JSON数値: {value}")

    return json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=pairs,
                      parse_constant=constant)


def integer(value: Any, minimum: int, maximum: int, label: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"整数契約が不一致: {label}")
    return value


def exact(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError(f"結果契約が不一致: {label}")


def validate_result(raw: bytes, case: str, returncode: int) -> dict[str, Any]:
    if type(returncode) is not int or returncode != 0:
        raise ValueError(f"mGBA終了コード: {returncode}")
    if case not in CASES:
        raise ValueError("未知のP05 case")
    ability, target_type, hit = CASES[case]
    result = strict_json(raw)
    expected = {
        "schema_version": 1, "status": "PASS", "scope": SCOPE, "case": case,
        "rom_sha256": ROM_ID["sha256"], "normal_controller_input": True,
        "passive_after_fixture": True, "fixture_battle_ram_overrides": True,
        "native_battle_setup": True, "representative_scheduler_e2e": True,
        "full_p05_acceptance": False, "species_ability_assignment_e2e": False,
        "save_reload_e2e": False, "release_ready": False, "warnings_errors": 0,
    }
    if not isinstance(result, dict) or set(result) != set(expected) | {"initial", "final", "events", "frames"}:
        raise ValueError("結果schemaが不一致")
    for key, value in expected.items():
        exact(result[key], value, key)
    frames = integer(result["frames"], 8, 18001, "frames")
    for name in ("initial", "final"):
        sample = result[name]
        if type(sample) is not dict or set(sample) != {"frame", "battle_flags", "pp", "hp", "abilities", "types"}:
            raise ValueError(f"sample schema: {name}")
        integer(sample["frame"], 0, 18001, name + ".frame")
        flags = integer(sample["battle_flags"], 0, 0xFFFFFFFF, name + ".battle_flags")
        if flags & ~4:
            raise ValueError("通常単体野生戦以外のroute flag")
        for field, limit in (("pp", 255), ("hp", 65535), ("abilities", 65535)):
            if type(sample[field]) is not list or len(sample[field]) != 2:
                raise ValueError(f"sample array: {name}.{field}")
            for item in sample[field]:
                integer(item, 0, limit, name + "." + field)
        types = sample["types"]
        if type(types) is not list or len(types) != 2:
            raise ValueError("type array")
        for row in types:
            if type(row) is not list or len(row) != 2:
                raise ValueError("type row")
            for item in row:
                integer(item, 0, 255, "type")
        exact(sample["abilities"], [ability, 0], name + ".abilities")
        exact(types, [[11, 11], [target_type, target_type]], name + ".types")
    initial, final = result["initial"], result["final"]
    exact(initial["frame"], 0, "initial frame")
    exact(final["battle_flags"], initial["battle_flags"], "battle route unchanged")
    exact(final["frame"], frames, "final frame")
    exact(initial["pp"], [35, 40], "initial PP")
    exact(final["pp"], [34, 39], "exactly one turn PP")
    exact(initial["hp"], [1000, 1000], "initial HP")
    exact(final["hp"][0], 1000, "Splash player HP")
    integer(final["hp"][1], 1, 999 if hit else 1000, "target HP")
    if not hit:
        exact(final["hp"][1], 1000, "Ghost immunity HP")
    events = result["events"]
    names = {"action", "move", "player_pp_spent", "enemy_pp_spent", "returned", "hit", "immune"}
    if type(events) is not dict or set(events) != names:
        raise ValueError("event schema")
    for key, value in events.items():
        integer(value, 0 if key in {"hit", "immune"} else 1, frames, "event." + key)
    if not (events["action"] < events["move"] < events["player_pp_spent"]
            <= events["enemy_pp_spent"] < events["returned"] < frames):
        raise ValueError("event order")
    observed, absent = ("hit", "immune") if hit else ("immune", "hit")
    if not events["player_pp_spent"] <= events[observed] < events["returned"]:
        raise ValueError("selected-move attribution")
    exact(events[absent], 0, "unexpected " + absent)
    return result


def prepare_output(path: Path, root: Path | None = None) -> Path:
    """Only owned files under .local are cleared; symlink ancestors are rejected."""
    root = ROOT if root is None else root
    local = root.absolute() / ".local"
    absolute = path.absolute()
    try:
        relative = absolute.relative_to(local)
    except ValueError as error:
        raise ValueError("出力先はrepository/.localの下に限定") from error
    if not relative.parts or ".." in relative.parts:
        raise ValueError("専用の出力directoryが必要です")
    current = root.absolute()
    for part in (".local", *relative.parts):
        current /= part
        if current.is_symlink():
            raise ValueError(f"symlink出力は禁止: {current}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"directoryではありません: {current}")
    absolute.mkdir(parents=True, exist_ok=True)
    owned = ["result.json", "result.json.tmp", "failure.json"]
    owned += [f"{prefix}.{suffix}" for prefix in LOG_NAMES for suffix in ("stdout", "stderr", "process.json")]
    for name in owned:
        target = absolute / name
        if target.is_dir():
            raise ValueError(f"file出力先がdirectoryです: {target}")
        target.unlink(missing_ok=True)
    return absolute


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_logged(command: list[str], cwd: Path, output: Path,
               prefix: str, timeout: float) -> int:
    if prefix not in LOG_NAMES:
        raise ValueError("未知のlog prefix")
    record: dict[str, Any] = {"command": command, "returncode": None, "timed_out": False}
    try:
        with (output / f"{prefix}.stdout").open("wb") as stdout, (output / f"{prefix}.stderr").open("wb") as stderr:
            completed = subprocess.run(command, cwd=cwd, stdout=stdout, stderr=stderr,
                                       timeout=timeout, check=False)
        record["returncode"] = completed.returncode
        return completed.returncode
    except subprocess.TimeoutExpired:
        record["timed_out"] = True
        raise
    except OSError as error:
        record["launch_error"] = str(error)
        raise
    finally:
        write_json(output / f"{prefix}.process.json", record)


def verify_unchanged(bindings: dict[Path, dict[str, Any]]) -> None:
    for path, expected in bindings.items():
        if identity(path) != expected:
            raise ValueError(f"入力/sourceが実行中に変更されました: {path}")


def run(output: Path) -> dict[str, Any]:
    output = prepare_output(output)
    bindings: dict[Path, dict[str, Any]] = {}
    try:
        cfg = strict_json((ROOT / CONFIG).read_bytes())
        row = cfg["runtime_candidate"]["rom"]
        if {"size": row["size"], "sha256": row["sha256"]} != ROM_ID:
            raise ValueError("Stage80候補identity契約が不一致")
        rom = ROOT / row["path"]
        rom.resolve().relative_to(ROOT.resolve())
        if identity(rom) != ROM_ID or identity(ROOT / BASELINE) != BASELINE_ID:
            raise ValueError("固定ROM/Stage62基準が不一致")
        bindings[rom] = ROM_ID
        for name, expected in DEPENDENCIES.items():
            if identity(ROOT / name) != expected:
                raise ValueError(f"共有runner固定版が不一致: {name}")
        for name in (SOURCE, HEADER, SCRIPT, CONFIG, BASELINE, *DEPENDENCIES):
            bindings[ROOT / name] = identity(ROOT / name)
        cases = []
        with tempfile.TemporaryDirectory(prefix="p05-scheduler-", dir=ROOT / ".local") as temporary:
            work = Path(temporary)
            executable = work / "runner"
            compile_command = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                               "-Itools", SOURCE, "-lmgba", "-o", str(executable)]
            if run_logged(compile_command, ROOT, output, "compile", 120) != 0:
                raise ValueError("strict C compile失敗")
            executable_id = identity(executable)
            for case in CASES:
                private_rom = work / f"{case}.gba"
                shutil.copyfile(rom, private_rom)
                private_rom.chmod(0o444)
                monitored = {**bindings, private_rom: ROM_ID, executable: executable_id}
                try:
                    code = run_logged([str(executable), str(private_rom), ROM_ID["sha256"], case],
                                      ROOT, output, case, 900)
                finally:
                    verify_unchanged(monitored)
                result = validate_result((output / f"{case}.stdout").read_bytes(), case, code)
                cases.append({"case": case, "returncode": code, "runner_result": result,
                              "stdout": identity(output / f"{case}.stdout"),
                              "stderr": identity(output / f"{case}.stderr"),
                              "process": identity(output / f"{case}.process.json")})
        verify_unchanged(bindings)
        report = {
            "schema_version": 1, "status": "PASS", "scope": SCOPE,
            "source_bindings": {str(p.relative_to(ROOT)): row for p, row in bindings.items() if p != rom},
            "rom": ROM_ID, "executable": executable_id, "cases": cases,
            "fresh_process_runs": len(CASES), "cached_results_reused": 0,
            "full_p05_acceptance": False, "release_ready": False,
            "active_baseline_changed": False,
        }
        write_json(output / "result.json.tmp", report)
        os.replace(output / "result.json.tmp", output / "result.json")
        return report
    except Exception as error:
        (output / "result.json").unlink(missing_ok=True)
        (output / "result.json.tmp").unlink(missing_ok=True)
        write_json(output / "failure.json", {"status": "FAIL", "error_type": type(error).__name__,
                                             "error": str(error), "release_ready": False})
        raise
    finally:
        if bindings:
            try:
                verify_unchanged(bindings)
            except Exception as error:
                (output / "result.json").unlink(missing_ok=True)
                write_json(output / "failure.json", {"status": "FAIL", "error_type": type(error).__name__,
                                                     "error": str(error), "release_ready": False})
                raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, default=ROOT / ".local/p05-controller-witness")
    args = parser.parse_args()
    print(json.dumps(run(args.output_directory), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
