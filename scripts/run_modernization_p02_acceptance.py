#!/usr/bin/env python3
"""P02進化受入のslot優先度修正を生成し、実ROM consumerを2 mGBA processで検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path("config/modernization_p02_acceptance_gate.json")
TASK = "USER-MODERNIZATION-P02-ACCEPTANCE"


class ModernizationP02AcceptanceError(RuntimeError):
    """P02 acceptance入力、patch、実行結果、または公開証跡の違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP02AcceptanceError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    absolute = path if path.is_absolute() else ROOT / path
    try:
        value = json.loads(absolute.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"JSONを読めません: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _workspace_path(relative: str, label: str) -> Path:
    path = ROOT / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(ROOT.resolve())
    except (OSError, ValueError) as error:
        _fail(f"{label}がworkspace通常ファイルではありません: {relative}: {error}")
    if path.is_symlink() or not resolved.is_file():
        _fail(f"{label}がworkspace通常ファイルではありません: {relative}")
    return resolved


def _fixed(contract: Mapping[str, Any], label: str) -> bytes:
    path = _workspace_path(str(contract.get("path", "")), label)
    raw = path.read_bytes()
    if len(raw) != int(contract.get("size", -1)):
        _fail(f"{label} size不一致")
    if _sha(raw) != str(contract.get("sha256", "")):
        _fail(f"{label} SHA-256不一致")
    return raw


def _source_identity(relative: str) -> dict[str, Any]:
    raw = _workspace_path(relative, "source").read_bytes()
    return {"path": relative, "size": len(raw), "sha256": _sha(raw)}


def _config_relative(config_path: Path) -> str:
    absolute = config_path if config_path.is_absolute() else ROOT / config_path
    try:
        return absolute.resolve(strict=True).relative_to(ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        _fail("acceptance configはworkspace内の通常ファイルでなければなりません")


def _hex_int(value: Any, label: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        _fail(f"{label}は0x付き16進数ではありません")
    try:
        result = int(value, 16)
    except ValueError:
        _fail(f"{label}が不正です")
    return result


def _validate_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != 1 or config.get("task") != TASK:
        _fail("acceptance config schema/task不一致")
    runtime = config.get("runtime", {})
    if int(runtime.get("process_runs", -1)) != 2:
        _fail("acceptance gateはexactly 2 independent processes必須です")
    repair = config.get("repair", {})
    rows = repair.get("repairs")
    if (
        repair.get("classification") != "TABLE_SLOT_PRIORITY_ROOT_FIX"
        or int(repair.get("stride", -1)) != 128
        or int(repair.get("entry_size", -1)) != 8
        or not isinstance(rows, list)
        or len(rows) != 6
    ):
        _fail("slot priority repair contract不一致")
    species = [int(row.get("species_id", -1)) for row in rows]
    if species != [499, 759, 861, 993, 1001, 1121]:
        _fail("slot priority repair species集合/順序不一致")


def _validate_static_rows(
    contract: Mapping[str, Any], repairs: list[Mapping[str, Any]],
) -> None:
    table_rows = contract.get("current_table", {}).get("rows")
    if not isinstance(table_rows, list):
        _fail("static evolution contractにcurrent rowsがありません")
    by_key: dict[tuple[int, int], Mapping[str, Any]] = {}
    for row in table_rows:
        if not isinstance(row, dict):
            _fail("static evolution rowがobjectではありません")
        source = row.get("source", {})
        by_key[(int(source.get("canonical_id", -1)), int(row.get("slot", -1)))] = row
    for repair in repairs:
        species = int(repair["species_id"])
        expected = (
            ("EVO_LEVEL_HOLD_ITEM", repair["conditional_before"]),
            ("EVO_LEVEL", repair["regular_before"]),
        )
        for slot, (method, raw) in enumerate(expected):
            row = by_key.get((species, slot))
            if row is None or row.get("method", {}).get("key") != method:
                _fail(f"static evolution row method不一致: species={species} slot={slot}")
            values = [
                int(row["method"]["id"]),
                int(row["condition"]["parameter"]["value"]),
                int(row["target"]["canonical_id"]),
                int(row["condition"]["extra"]["value"]),
            ]
            if values != [int(value) for value in raw]:
                _fail(f"static evolution row tuple不一致: species={species} slot={slot}")


def _validate_rayquaza_gate(value: Mapping[str, Any]) -> None:
    claims = value.get("claims", {})
    cases = value.get("runtime_result", {}).get("cases", {})
    if (
        value.get("status") != "PASS"
        or value.get("classification")
        != "DIRECT_CALL_BOUNDED_NOT_SCHEDULER_E2E"
        or claims.get("exact_stage64_rom") is not True
        or claims.get("dragon_ascent_630_selects_mega_rayquaza_1092") is not True
        or claims.get("historical_773_does_not_select_wish_mega") is not True
        or claims.get("null_moves_does_not_select_wish_mega") is not True
        or claims.get("full_evolution_acceptance") is not False
        or cases.get("dragon_ascent", {}).get("result") != 1092
        or cases.get("historical_773", {}).get("result") != 0
        or cases.get("null_moves", {}).get("result") != 0
    ):
        _fail("既存Rayquaza実ROM縦切りを継承できません")


def build_candidate(
    config: Mapping[str, Any], *, parent_bytes: bytes | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Stage66をexact preimage検査し、6組のrow順序だけを交換する。"""

    _validate_config(config)
    parent_contract = config["inputs"]["parent_rom"]
    parent = _fixed(parent_contract, "parent ROM") if parent_bytes is None else parent_bytes
    if len(parent) != int(parent_contract["size"]):
        _fail("supplied parent ROM size不一致")
    if _sha(parent) != str(parent_contract["sha256"]):
        _fail("supplied parent ROM SHA-256不一致")

    repair = config["repair"]
    base = _hex_int(repair["table_rom_offset"], "table_rom_offset")
    stride = int(repair["stride"])
    entry_size = int(repair["entry_size"])
    output = bytearray(parent)
    rows: list[dict[str, Any]] = []
    declared_spans: list[list[int]] = []
    for row in repair["repairs"]:
        species = int(row["species_id"])
        first = base + species * stride
        second = first + entry_size
        before_first = bytes(output[first:first + entry_size])
        before_second = bytes(output[second:second + entry_size])
        expected_first = struct.pack(
            "<HHHH", *[int(value) for value in row["conditional_before"]],
        )
        expected_second = struct.pack(
            "<HHHH", *[int(value) for value in row["regular_before"]],
        )
        if before_first != expected_first or before_second != expected_second:
            _fail(f"slot repair preimage不一致: species={species}")
        output[first:first + entry_size] = expected_second
        output[second:second + entry_size] = expected_first
        declared_spans.append([first, second + entry_size])
        rows.append({
            "species_id": species,
            "source": row["source"],
            "span": [first, second + entry_size],
            "before": [row["conditional_before"], row["regular_before"]],
            "after": [row["regular_before"], row["conditional_before"]],
        })

    candidate = bytes(output)
    changed_offsets = [
        index
        for index, (before, after) in enumerate(zip(parent, candidate, strict=True))
        if before != after
    ]
    if len(changed_offsets) != 60:
        _fail(f"slot repair changed byte count不一致: {len(changed_offsets)}")
    if any(
        not any(start <= offset < end for start, end in declared_spans)
        for offset in changed_offsets
    ):
        _fail("slot repairが宣言span外を変更しました")
    candidate_contract = config["candidate_rom"]
    if len(candidate) != int(candidate_contract["size"]):
        _fail("candidate ROM size不一致")
    if _sha(candidate) != str(candidate_contract["sha256"]):
        _fail("candidate ROM SHA-256不一致")
    return candidate, {
        "classification": repair["classification"],
        "parent": parent_contract,
        "candidate": candidate_contract,
        "rows": rows,
        "changed_byte_count": len(changed_offsets),
        "changed_rom_offsets": changed_offsets,
        "outside_declared_spans": 0,
        "retained_output_rom": False,
    }


def _static_inputs(
    config_path: Path, config: Mapping[str, Any],
    *, parent_bytes: bytes | None = None,
) -> tuple[dict[str, Any], bytes]:
    _validate_config(config)
    candidate, repair_audit = build_candidate(config, parent_bytes=parent_bytes)
    rayquaza_raw = _fixed(
        config["inputs"]["rayquaza_runtime_gate"], "Rayquaza runtime gate",
    )
    static_raw = _fixed(
        config["inputs"]["static_evolution_contract"], "static evolution contract",
    )
    try:
        rayquaza = json.loads(rayquaza_raw)
        static = json.loads(static_raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"固定P02入力がJSONではありません: {error}")
    if not isinstance(rayquaza, dict) or not isinstance(static, dict):
        _fail("固定P02入力のJSON rootがobjectではありません")
    _validate_rayquaza_gate(rayquaza)
    _validate_static_rows(static, config["repair"]["repairs"])

    runtime = config["runtime"]
    symbol_entries: list[dict[str, Any]] = []
    for name, address_text in runtime["symbols"].items():
        address = _hex_int(address_text, name)
        offset = address - 0x08000000
        expected = bytes.fromhex(runtime["expected_entry_bytes"][name])
        actual = candidate[offset:offset + len(expected)]
        if actual != expected:
            _fail(f"runtime symbol entry bytes不一致: {name}")
        symbol_entries.append({
            "name": name,
            "address": address_text,
            "entry_bytes": actual.hex(),
        })

    lib = runtime["libmgba"]
    lib_path = Path(str(lib["path"]))
    if lib_path.is_symlink() or not lib_path.is_file():
        _fail("固定libmGBAが通常ファイルではありません")
    lib_raw = lib_path.read_bytes()
    if _sha(lib_raw) != str(lib["sha256"]):
        _fail("libmGBA SHA-256不一致")
    sources = [
        _source_identity(runtime["gate_script"]),
        _source_identity(runtime["runner_source"]),
        *[_source_identity(path) for path in runtime["transitive_sources"]],
    ]
    return {
        "config": _source_identity(_config_relative(config_path)),
        "parent_rom": config["inputs"]["parent_rom"],
        "candidate_rom": config["candidate_rom"],
        "rayquaza_runtime_gate": config["inputs"]["rayquaza_runtime_gate"],
        "static_evolution_contract": config["inputs"]["static_evolution_contract"],
        "rayquaza_claims_inherited": True,
        "repair": repair_audit,
        "symbols": symbol_entries,
        "sources": sources,
        "libmgba": {
            "path": str(lib_path),
            "size": len(lib_raw),
            "sha256": _sha(lib_raw),
        },
    }, candidate


def _validate_runner_result(
    result: Mapping[str, Any], config: Mapping[str, Any],
) -> None:
    cases = result.get("cases", {})
    required_cases = {
        "level_below": 0,
        "level_boundary": 2,
        "level_above": 2,
        "friendship_below": 0,
        "friendship_boundary": 13,
        "item_positive": 20,
        "item_wrong": 0,
        "item_missing": 0,
        "move_positive": 735,
        "move_missing": 0,
        "trade_positive": 453,
        "trade_item_positive": 536,
        "trade_item_missing": 0,
        "level_item_below": 0,
        "level_item_missing": 500,
        "level_item_boundary": 1419,
        "night_form_below": 0,
        "night_form_boundary": 1220,
    }
    if (
        result.get("schema_version") != 1
        or result.get("status") != "PASS"
        or result.get("classification") != "DIRECT_REAL_CONSUMER_CHECKPOINT"
        or result.get("rom_sha256") != config["candidate_rom"]["sha256"]
        or result.get("read_only_rom") is not True
        or int(result.get("boot_trace_segments", -1)) != 233
        or set(cases) != set(required_cases)
        or int(result.get("warnings_errors", -1)) != 0
        or result.get("artifacts_written") != []
    ):
        _fail("mGBA acceptance runner top-level contract不一致")
    for key, expected in required_cases.items():
        row = cases[key]
        if (
            int(row.get("expected", -1)) != expected
            or int(row.get("result", -1)) != expected
            or int(row.get("instructions", 0)) <= 0
            or row.get("payload_pc_seen") is not True
        ):
            _fail(f"mGBA acceptance case不一致: {key}")
    consume = result.get("trade_item_consumption", {})
    if consume.get("item_before") != 477 or consume.get("item_after") != 0:
        _fail("trade item consumption不一致")
    repair = result.get("level_item_priority_repair", {})
    required_repair_flags = (
        "correct_item_selects_conditional_form",
        "correct_item_consumed_after_selection",
        "below_level_retains_item",
        "wrong_item_selects_regular_form_and_is_retained",
        "missing_item_selects_regular_form",
    )
    if (
        repair.get("repaired_species_count") != 6
        or any(repair.get(key) is not True for key in required_repair_flags)
        or int(repair.get("instruction_total", 0)) <= 0
    ):
        _fail("level-held-item priority repair runtime不一致")
    application = result.get("target_application", {})
    if (
        application.get("classification") != "ROM_CONSUMERS_WITHOUT_ASYNC_SCENE"
        or application.get("source") != 475
        or application.get("selected_target") != 735
        or application.get("applied_species") != 735
        or application.get("personality_before")
        != application.get("personality_after")
        or application.get("ability_selector_before")
        != application.get("ability_selector_after")
        or application.get("hidden_ability_bit_preserved") is not True
        or application.get("moves_before") != [246, 33, 45, 52]
        or application.get("moves_after") != [246, 33, 45, 52]
    ):
        _fail("target application identity contract不一致")


def _run_processes(
    executable: Path, rom_path: Path, sha256: str, count: int, timeout: int,
) -> list[dict[str, Any]]:
    processes = [
        subprocess.Popen(
            [str(executable), str(rom_path), sha256],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(count)
    ]
    if len({process.pid for process in processes}) != count:
        _fail("独立mGBA process IDが重複しました")
    results: list[dict[str, Any]] = []
    try:
        for process in processes:
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode != 0:
                _fail(f"mGBA acceptance runner failed ({process.returncode}): {stderr.strip()}")
            if stderr:
                _fail(f"mGBA acceptance runnerがstderrを出力しました: {stderr.strip()}")
            try:
                value = json.loads(stdout)
            except json.JSONDecodeError as error:
                _fail(f"mGBA acceptance runner出力がJSONではありません: {error}")
            if not isinstance(value, dict):
                _fail("mGBA acceptance runner JSON rootがobjectではありません")
            results.append(value)
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    if any(value != results[0] for value in results[1:]):
        _fail("独立2 mGBA processの結果が一致しません")
    return results


def run_gate(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = _read_json(config_path)
    static, candidate = _static_inputs(config_path, config)
    runtime = config["runtime"]
    compiler = shutil.which(str(runtime["compiler"]))
    if compiler is None:
        _fail("C compilerがありません")
    version = subprocess.run(
        [compiler, "--version"], cwd=ROOT, capture_output=True,
        text=True, check=False,
    )
    if version.returncode != 0 or not version.stdout.splitlines():
        _fail("C compiler versionを取得できません")

    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p02-acceptance-", dir=local) as raw:
        temporary = Path(raw)
        executable = temporary / "p02-acceptance-smoke"
        rom_path = temporary / "p02-overlay-parent.gba"
        rom_path.write_bytes(candidate)
        command = [
            compiler,
            *map(str, runtime["compile_flags"]),
            str(ROOT / runtime["runner_source"]),
            "-o",
            str(executable),
            *map(str, runtime["link_flags"]),
        ]
        compiled = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True,
            timeout=int(runtime["timeout_seconds"]), check=False,
        )
        if compiled.returncode != 0:
            _fail(f"mGBA acceptance compile failed: {compiled.stdout}{compiled.stderr}")
        if compiled.stdout or compiled.stderr:
            _fail("mGBA acceptance compileが予期しない出力を生成しました")
        results = _run_processes(
            executable,
            rom_path,
            _sha(candidate),
            int(runtime["process_runs"]),
            int(runtime["timeout_seconds"]),
        )
    for result in results:
        _validate_runner_result(result, config)
    runtime_result = results[0]
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "CHECKPOINT_NOT_DONE",
        "classification": "ACTUAL_CONSUMER_PARTIAL_ACCEPTANCE_WITH_ROOT_FIX",
        "inputs": static,
        "execution": {
            "process_runs": 2,
            "independent_processes": True,
            "identical_results": True,
            "compiler": compiler,
            "compiler_version": version.stdout.splitlines()[0],
            "compile_flags": runtime["compile_flags"],
            "link_flags": runtime["link_flags"],
            "runner_result_sha256": _sha(_stable(runtime_result)),
        },
        "runtime_result": runtime_result,
        "completed_acceptance": [
            "level成立/不成立/境界",
            "friendship成立/不成立/境界",
            "item parameter成立/誤値/欠落",
            "known move成立/不成立",
            "trade成立とtrade item消費/不足",
            "昼夜formのnight成立/level境界",
            "6種のlevel+held-item分岐優先度と成功時だけの道具消費",
            "target選択の非破壊性",
            "実SetMonData/CalculateMonStats後の4技・個体ID・ability slot保持",
            "Stage64 Rayquaza Wish-Mega実ROM縦切りの継承",
        ],
        "remaining_acceptance": [
            "通常UI schedulerからの進化完走とBキャンセル",
            "bag item使用UIの在庫減算とbag在庫不足",
            "進化時新規技、4技満杯、技習得キャンセル",
            "通常/隠れ特性と全formの進化scene後処理",
            "通常save、終了、fresh core Continue後の進化済み個体同一性",
            "通信代替UIと昼条件の代表回帰",
        ],
        "claims": {
            "exact_p02_overlay_parent": True,
            "real_get_evolution_target_species_executed": True,
            "real_item_evolution_removal_executed": True,
            "level_held_item_slot_priority_root_fixed": True,
            "correct_condition_item_only_consumed": True,
            "rayquaza_stage64_gate_inherited": True,
            "target_application_rom_consumers_executed": True,
            "async_evolution_scene_scheduler_e2e": False,
            "cancel_e2e": False,
            "bag_inventory_consumer_e2e": False,
            "evolution_move_learning_e2e": False,
            "post_scene_ability_form_e2e": False,
            "fresh_core_save_reload_e2e": False,
            "full_evolution_acceptance": False,
        },
        "release_ready": False,
        "artifacts_written": [config["output"]],
    }


def _validate_published(
    evidence: Mapping[str, Any], config: Mapping[str, Any],
    static: Mapping[str, Any],
) -> None:
    claims = evidence.get("claims", {})
    if (
        evidence.get("schema_version") != 1
        or evidence.get("task") != TASK
        or evidence.get("status") != "CHECKPOINT_NOT_DONE"
        or evidence.get("classification")
        != "ACTUAL_CONSUMER_PARTIAL_ACCEPTANCE_WITH_ROOT_FIX"
        or evidence.get("inputs") != static
        or evidence.get("execution", {}).get("process_runs") != 2
        or evidence.get("execution", {}).get("independent_processes") is not True
        or evidence.get("execution", {}).get("identical_results") is not True
        or claims.get("level_held_item_slot_priority_root_fixed") is not True
        or claims.get("correct_condition_item_only_consumed") is not True
        or claims.get("rayquaza_stage64_gate_inherited") is not True
        or claims.get("full_evolution_acceptance") is not False
        or evidence.get("release_ready") is not False
        or evidence.get("artifacts_written") != [config["output"]]
    ):
        _fail("公開済みP02 acceptance checkpoint不一致")
    _validate_runner_result(evidence.get("runtime_result", {}), config)
    if evidence["execution"].get("runner_result_sha256") != _sha(
        _stable(evidence["runtime_result"]),
    ):
        _fail("公開済みrunner result hash不一致")


def validate_published_gate(
    config_path: Path = DEFAULT_CONFIG,
    *, parent_bytes: bytes | None = None,
) -> dict[str, Any]:
    config = _read_json(config_path)
    static, _candidate = _static_inputs(
        config_path, config, parent_bytes=parent_bytes,
    )
    evidence = _read_json(Path(config["output"]))
    _validate_published(evidence, config, static)
    return evidence


def _write(path: Path, raw: bytes) -> None:
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", delete=False,
    ) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    os.replace(temporary, destination)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        config = _read_json(args.config)
        if args.mode == "run":
            evidence = run_gate(args.config)
            _write(Path(config["output"]), _stable(evidence))
        else:
            evidence = validate_published_gate(args.config)
    except (
        KeyError,
        OSError,
        struct.error,
        subprocess.SubprocessError,
        TypeError,
        ValueError,
        ModernizationP02AcceptanceError,
    ) as error:
        print(
            f"MODERNIZATION_P02_ACCEPTANCE_{args.mode.upper()}=FAIL",
            file=sys.stderr,
        )
        print(str(error), file=sys.stderr)
        return 1
    print(
        f"MODERNIZATION_P02_ACCEPTANCE_{args.mode.upper()}=PASS "
        f"status={evidence['status']} "
        f"processes={evidence['execution']['process_runs']} "
        f"root_fix={evidence['claims']['level_held_item_slot_priority_root_fixed']} "
        f"full_acceptance={evidence['claims']['full_evolution_acceptance']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
