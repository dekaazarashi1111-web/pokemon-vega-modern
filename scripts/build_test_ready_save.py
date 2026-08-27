#!/usr/bin/env python3
"""Stage56以降の標準テスト用saveを通常ROM APIだけで生成・検証する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/test_ready_save.json"
RUNNER_SOURCE = ROOT / "tools/mgba_test_ready_save.c"
BOOTSTRAP_SOURCE = ROOT / "tools/mgba_codex_battle_ipad_bootstrap.c"
BATTLE_CORE_SOURCE = ROOT / "tools/mgba_battle_core_smoke.c"


class TestReadySaveError(RuntimeError):
    pass


def _fail(message: str) -> None:
    raise TestReadySaveError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"JSONを読めません: {path}: {exc}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_bytes_atomic(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(value)
    os.replace(temporary, path)


def _manifest(path: Path, key_field: str) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get(key_field, "")
        if not key or key in result:
            _fail(f"manifest keyが空または重複しています: {path}: {key}")
        result[key] = row
    return result


def _source_hashes() -> dict[str, str]:
    paths = (
        DEFAULT_CONFIG,
        RUNNER_SOURCE,
        BOOTSTRAP_SOURCE,
        BATTLE_CORE_SOURCE,
    )
    return {str(path.relative_to(ROOT)): _sha256(path) for path in paths}


def validate_profile(config: dict[str, Any], *, require_rom: bool = True) -> None:
    if config.get("schema_version") != 1:
        _fail("profile schema_versionが1ではありません")
    if config.get("profile_key") != "STAGE56_TEST_READY_V1":
        _fail("標準profile keyが一致しません")

    input_config = config.get("input")
    output = config.get("output")
    field = config.get("field")
    if not isinstance(input_config, dict) or not isinstance(output, dict):
        _fail("input/output設定がありません")
    if field != {
        "map_group": 96,
        "map_number": 5,
        "x": 20,
        "y": 20,
        "role": "CODEX_BATTLE_RECEPTION_FRONT",
    }:
        _fail("Codex受付前field profileが一致しません")
    if output.get("size") != 0x20000 or output.get("save_generations") != 2:
        _fail("save size/generation契約が一致しません")

    rom = ROOT / str(input_config.get("rom", ""))
    save = ROOT / str(output.get("save", ""))
    if rom.stem != save.stem:
        _fail("ROMとsaveのbasenameが一致しません")
    if require_rom:
        if not rom.is_file() or rom.stat().st_size != input_config.get("size"):
            _fail("Stage56 ROMが存在しないかsizeが一致しません")
        if _sha256(rom) != input_config.get("sha256"):
            _fail("Stage56 ROM SHA-256が一致しません")

    progression = config.get("progression_flags")
    if not isinstance(progression, list) or [row.get("id") for row in progression] != [
        0x0828,
        0x0829,
        0x082F,
    ]:
        _fail("博士／図鑑／ランニングシューズflagが一致しません")
    obedience = config.get("obedience")
    if not isinstance(obedience, dict):
        _fail("服従profileがありません")
    if obedience.get("badge_flags") != list(range(0x0820, 0x0828)):
        _fail("全8 badge flagが一致しません")
    if obedience.get("max_obedient_level") != 100:
        _fail("服従上限がLv.100ではありません")

    party = config.get("party")
    if not isinstance(party, list) or len(party) != 6:
        _fail("標準partyが6体ではありません")
    if [row.get("slot") for row in party] != list(range(1, 7)):
        _fail("標準party slotが1..6ではありません")
    species = _manifest(ROOT / "manifests/species_ids.csv", "species_key")
    items = _manifest(ROOT / "manifests/item_ids.csv", "item_key")
    moves = _manifest(ROOT / "manifests/move_ids.csv", "move_key")
    for row in party:
        key = row.get("species_key")
        if key not in species or int(species[key]["id"]) != row.get("species_id"):
            _fail(f"party Species canonical IDが一致しません: {key}")
    lead = party[0]
    if (
        lead.get("species_key") != "SPECIES_KEY_MEWTWO"
        or lead.get("species_id") != 150
        or lead.get("level") != 100
        or lead.get("held_item_key") != "ITEM_KEY_MEWTWONITE_Y"
        or lead.get("held_item_id") != 761
    ):
        _fail("先頭Lv.100ミュウツーprofileが一致しません")
    item_key = str(lead["held_item_key"])
    if item_key not in items or int(items[item_key]["id"]) != lead["held_item_id"]:
        _fail("ミュウツナイトY canonical IDが一致しません")
    if party[1].get("species_key") != "SPECIES_KEY_VEGA_007" or party[1].get("level") != 5:
        _fail("博士のアクタシがslot 2にありません")

    move_rows = lead.get("moves")
    expected_move_ids = [94, 58, 85, 366]
    if not isinstance(move_rows, list) or [row.get("move_id") for row in move_rows] != expected_move_ids:
        _fail("ミュウツーの4攻撃技が一致しません")
    for row in move_rows:
        key = row.get("move_key")
        if key not in moves or int(moves[key]["id"]) != row.get("move_id"):
            _fail(f"move canonical IDが一致しません: {key}")

    catalog = _read_json(ROOT / "content/codex_battle/catalog.json")
    move_catalog = {row["id"]: row for row in catalog.get("moves", [])}
    selected = [move_catalog.get(move_id) for move_id in expected_move_ids]
    if any(row is None for row in selected):
        _fail("4技がCodex catalogにありません")
    if any(row["category"] == 0 or row["power"] <= 0 for row in selected):
        _fail("4技に変化技が混入しています")
    if len({row["type"] for row in selected}) != 4:
        _fail("4技の攻撃typeが重複しています")
    if [row["pp"] for row in selected] != [10, 10, 15, 20]:
        _fail("4技の基礎PPが一致しません")

    policy = config.get("generation_policy")
    required_apis = {
        "FlagSet",
        "CreateMon",
        "SetMonData",
        "CalculatePP",
        "CalculateMonStats",
        "GetSetPokedexFlag",
        "TrySavingData",
    }
    if not isinstance(policy, dict) or set(policy.get("rom_apis", [])) != required_apis:
        _fail("通常ROM API契約が一致しません")
    if policy.get("host_side_save_edit") is not False:
        _fail("host-side save editが禁止されていません")
    if policy.get("deterministic_process_runs") != 2:
        _fail("決定性process回数が2ではありません")


def _compile_runner(binary: Path) -> None:
    binary.parent.mkdir(parents=True, exist_ok=True)
    compiler = shlex.split(os.environ.get("CC", "cc"))
    if not compiler:
        _fail("C compilerが設定されていません")
    command = compiler + [
        "-std=c11",
        "-O2",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(RUNNER_SOURCE),
        "-o",
        str(binary),
        "-lmgba",
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        _fail(f"mGBA runner compile失敗:\n{result.stdout}{result.stderr}")


def _run_runner(binary: Path, rom: Path, save: Path) -> dict[str, Any]:
    result = subprocess.run(
        [str(binary), str(rom), str(save)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        _fail(f"mGBA save生成失敗:\n{result.stdout}{result.stderr}")
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        _fail("mGBA runner JSONがありません")
    try:
        report = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        _fail(f"mGBA runner JSONが不正です: {exc}")
    if not isinstance(report, dict) or report.get("status") != "PASS":
        _fail("mGBA runnerがPASSではありません")
    return report


def _validate_runner_report(config: dict[str, Any], report: dict[str, Any]) -> None:
    lead = config["party"][0]
    expected = {
        "schema_version": 1,
        "rom_sha256": config["input"]["sha256"],
        "save_size": config["output"]["size"],
        "save_generations": 2,
        "slot0_fresh_load": True,
        "slot1_fresh_load": True,
        "natural_continue": True,
        "codex_reception_visible": True,
        "progression_flags": [0x0828, 0x0829, 0x082F],
        "badge_flags": list(range(0x0820, 0x0828)),
        "party_species": [row["species_id"] for row in config["party"]],
        "party_levels": [row["level"] for row in config["party"]],
        "warnings": 0,
    }
    for key, value in expected.items():
        if report.get(key) != value:
            _fail(f"mGBA report {key}がprofileと一致しません")
    if report.get("map") != {"group": 96, "number": 5, "x": 20, "y": 20}:
        _fail("mGBA report fieldが一致しません")
    if report.get("lead") != {
        "species_id": lead["species_id"],
        "level": lead["level"],
        "held_item_id": lead["held_item_id"],
        "moves": [row["move_id"] for row in lead["moves"]],
        "pp": [10, 10, 15, 20],
    }:
        _fail("mGBA reportの先頭ミュウツーが一致しません")


def build(config_path: Path) -> dict[str, Any]:
    config = _read_json(config_path)
    validate_profile(config)
    rom = ROOT / config["input"]["rom"]
    output = ROOT / config["output"]["save"]
    report_path = ROOT / config["output"]["report"]
    binary = ROOT / ".local/mgba-test-ready-save"
    _compile_runner(binary)

    local_root = ROOT / ".local"
    local_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="test-ready-save-", dir=local_root) as temporary:
        directory = Path(temporary)
        saves = [directory / "run1.srm", directory / "run2.srm"]
        reports = [_run_runner(binary, rom, save) for save in saves]
        for report in reports:
            _validate_runner_report(config, report)
        first = saves[0].read_bytes()
        second = saves[1].read_bytes()
        if first != second:
            _fail("独立2 processのsaveがbyte一致しません")
        if reports[0] != reports[1]:
            _fail("独立2 processのmGBA証跡が一致しません")
        _write_bytes_atomic(output, first)

    save_sha256 = _sha256(output)
    if reports[0].get("save_sha256") != save_sha256:
        _fail("runnerと出力saveのSHA-256が一致しません")
    result = {
        "schema_version": 1,
        "task": config["task"],
        "status": "PASS",
        "profile_key": config["profile_key"],
        "input": {
            "rom": str(rom.relative_to(ROOT)),
            "size": rom.stat().st_size,
            "sha256": _sha256(rom),
        },
        "output": {
            "save": str(output.relative_to(ROOT)),
            "size": output.stat().st_size,
            "sha256": save_sha256,
        },
        "determinism": {
            "process_runs": 2,
            "byte_identical": True,
        },
        "profile": {
            "field": config["field"],
            "progression_flags": config["progression_flags"],
            "obedience": config["obedience"],
            "party": config["party"],
        },
        "mgba": reports[0],
        "source_hashes": _source_hashes(),
        "ipad_required_for_pass": False,
    }
    _write_json_atomic(report_path, result)
    print(
        "Stage56 standard test-ready save: PASS "
        f"sha256={save_sha256} size={output.stat().st_size}"
    )
    return result


def check(config_path: Path) -> dict[str, Any]:
    config = _read_json(config_path)
    validate_profile(config)
    output = ROOT / config["output"]["save"]
    report_path = ROOT / config["output"]["report"]
    if not output.is_file() or output.stat().st_size != config["output"]["size"]:
        _fail("生成済み標準saveが存在しないかsizeが一致しません")
    report = _read_json(report_path)
    if report.get("status") != "PASS" or report.get("profile_key") != config["profile_key"]:
        _fail("生成済み標準save reportがPASSではありません")
    if report.get("output") != {
        "save": str(output.relative_to(ROOT)),
        "size": output.stat().st_size,
        "sha256": _sha256(output),
    }:
        _fail("生成済み標準save identityがreportと一致しません")
    if report.get("source_hashes") != _source_hashes():
        _fail("標準save生成source hashが一致しません")
    _validate_runner_report(config, report.get("mgba", {}))
    print(
        "Stage56 standard test-ready save check: PASS "
        f"sha256={report['output']['sha256']}"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    try:
        if args.mode == "build":
            build(config_path)
        else:
            check(config_path)
    except (TestReadySaveError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"Stage56 standard test-ready save: FAIL: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
