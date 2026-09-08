#!/usr/bin/env python3
"""Stage64 exact ROMのRayquaza Wish-Megaを独立2 mGBA processで検証する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path("config/modernization_p02_mgba_gate.json")
TASK = "USER-MODERNIZATION-P02-MGBA-GATE"


class ModernizationP02MgbaError(RuntimeError):
    """mGBA gateの入力identity、ABI、または実行結果が不正。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP02MgbaError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"JSONを読めません: {path}: {error}")
    if not isinstance(value, dict):
        _fail(f"JSON rootがobjectではありません: {path}")
    return value


def _fixed(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract.get("path", ""))
    if path.is_symlink() or not path.is_file():
        _fail(f"{label}が通常ファイルではありません: {path}")
    raw = path.read_bytes()
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size不一致")
    if _sha(raw) != str(contract.get("sha256", "")):
        _fail(f"{label} SHA-256不一致")
    return raw


def _fixed_or_supplied(
    contract: Mapping[str, Any], label: str, supplied: bytes | None,
) -> bytes:
    if supplied is None:
        return _fixed(contract, label)
    if "size" in contract and len(supplied) != int(contract["size"]):
        _fail(f"{label} supplied size不一致")
    if _sha(supplied) != str(contract.get("sha256", "")):
        _fail(f"{label} supplied SHA-256不一致")
    return supplied


def _source_identity(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"runner sourceが通常ファイルではありません: {relative}")
    raw = path.read_bytes()
    return {"path": relative, "size": len(raw), "sha256": _sha(raw)}


def _parse_symbol(raw: bytes, symbol: str, label: str) -> int:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        _fail(f"{label}がASCIIではありません: {error}")
    match = re.search(rf"(?m)^{re.escape(symbol)}:\s+([0-9A-Fa-f]{{8}})\s*$", text)
    if match is None:
        _fail(f"{label}に{symbol}がありません")
    return int(match.group(1), 16)


def _static_inputs(
    config_path: Path,
    config: Mapping[str, Any],
    *,
    stage63_bytes: bytes | None = None,
    stage64_bytes: bytes | None = None,
) -> dict[str, Any]:
    if config.get("schema_version") != 1 or config.get("task") != TASK:
        _fail("mGBA config schema/task不一致")
    inputs = config["inputs"]
    stage63 = _fixed_or_supplied(inputs["stage63_rom"], "Stage63 ROM", stage63_bytes)
    stage64 = _fixed_or_supplied(inputs["stage64_rom"], "Stage64 ROM", stage64_bytes)
    static_contract = _fixed(inputs["p02_static_contract"], "P02 static contract")
    try:
        contract = json.loads(static_contract)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"P02 static contractがJSONではありません: {error}")
    policy = contract.get("runtime_contract", {}).get("producer", {}).get(
        "parameter_namespace_policy", {},
    )
    if (
        policy.get("status") != "PASS"
        or int(policy.get("legacy_resolved_parameter_id", -1)) != 773
        or int(policy.get("modernization_resolved_parameter_id", -1)) != 630
    ):
        _fail("P02 static contractがroot namespace fixを保証していません")

    stage64_config = _read_json(Path(inputs["stage64_config_path"]))
    if (
        stage64_config.get("inputs", {}).get("parent_rom", {}).get("sha256")
        != inputs["stage63_rom"]["sha256"]
        or stage64_config.get("outputs", {}).get("rom") != inputs["stage64_rom"]["path"]
    ):
        _fail("Stage64 builder configとmGBA gate inputが一致しません")

    patch = config["patch_contract"]
    offset = int(str(patch["entry_rom_offset"]), 16)
    before = struct.unpack_from("<HHHH", stage63, offset)
    after = struct.unpack_from("<HHHH", stage64, offset)
    if list(before) != list(patch["stage63_entry"]):
        _fail(f"Stage63 Rayquaza preimage不一致: {before}")
    if list(after) != list(patch["stage64_entry"]):
        _fail(f"Stage64 Rayquaza entry不一致: {after}")
    differences = [
        index
        for index, values in enumerate(zip(stage63, stage64, strict=True))
        if values[0] != values[1]
    ]
    if differences != list(patch["changed_rom_offsets"]):
        _fail(f"Stage63→64の変更範囲が2-byte contract外です: {differences[:16]}")

    offsets_contract = inputs["battle_core_offsets"]
    offset_rows = []
    for key in ("run_1_path", "run_2_path"):
        row = {
            "path": offsets_contract[key],
            "size": offsets_contract["size"],
            "sha256": offsets_contract["sha256"],
        }
        raw = _fixed(row, f"battle-core {key}")
        address = _parse_symbol(raw, "GetMegaSpecies", f"battle-core {key}")
        offset_rows.append({**row, "get_mega_species": f"0x{address:08X}"})
    expected_symbol = int(str(config["runtime"]["get_mega_species_symbol"]), 16)
    if any(int(row["get_mega_species"], 16) != expected_symbol for row in offset_rows):
        _fail("battle-core offsetsのGetMegaSpecies address不一致")

    sources = [
        _source_identity(config["runtime"]["gate_script"]),
        _source_identity(config["runtime"]["runner_source"]),
        *[_source_identity(path) for path in config["runtime"]["transitive_sources"]],
    ]
    lib = config["runtime"]["libmgba"]
    lib_path = Path(str(lib["path"]))
    if lib_path.is_symlink() or not lib_path.is_file():
        _fail(f"固定libmGBAが通常ファイルではありません: {lib_path}")
    lib_raw = lib_path.read_bytes()
    if _sha(lib_raw) != lib["sha256"]:
        _fail("libmGBA SHA-256不一致")
    return {
        "config": _source_identity(config_path.as_posix()),
        "stage63": {
            **inputs["stage63_rom"],
            "rayquaza_entry": list(before),
        },
        "stage64": {
            **inputs["stage64_rom"],
            "rayquaza_entry": list(after),
        },
        "p02_static_contract": inputs["p02_static_contract"],
        "battle_core_fingerprint": offsets_contract["fingerprint"],
        "offsets": offset_rows,
        "sources": sources,
        "libmgba": {
            "path": str(lib_path),
            "size": len(lib_raw),
            "sha256": _sha(lib_raw),
        },
        "changed_rom_offsets": differences,
    }


def _validate_runner_result(result: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    runtime = config["runtime"]
    expected = config["expectations"]
    if (
        result.get("schema_version") != 1
        or result.get("status") != "PASS"
        or result.get("classification") != "DIRECT_CALL_BOUNDED"
        or result.get("rom_sha256") != config["inputs"]["stage64_rom"]["sha256"]
        or result.get("read_only") is not True
        or result.get("get_mega_species_symbol") != runtime["get_mega_species_symbol"]
        or result.get("get_mega_species_thumb")
        != f"0x{int(runtime['get_mega_species_symbol'], 16) | 1:08X}"
        or int(result.get("species_id", -1)) != int(expected["species_id"])
        or int(result.get("target_species_id", -1)) != int(expected["target_species_id"])
        or int(result.get("item_id", -1)) != int(expected["item_id"])
        or result.get("payload_pc_seen") is not True
        or int(result.get("warnings_errors", -1)) != 0
        or result.get("artifacts_written") != []
    ):
        _fail("mGBA runner top-level contract不一致")
    cases = result.get("cases", {})
    required = {
        "dragon_ascent": (
            [int(expected["dragon_ascent_move_id"]), 0, 0, 0],
            int(expected["dragon_ascent_result"]),
        ),
        "historical_773": (
            [int(expected["historical_wrong_move_id"]), 0, 0, 0],
            int(expected["historical_wrong_result"]),
        ),
        "null_moves": (None, int(expected["null_moves_result"])),
    }
    if set(cases) != set(required):
        _fail("mGBA runner case集合不一致")
    for key, (moves, expected_result) in required.items():
        case = cases[key]
        if (
            case.get("moves") != moves
            or int(case.get("result", -1)) != expected_result
            or int(case.get("instructions", 0)) <= 0
        ):
            _fail(f"mGBA runner case不一致: {key}")


def _run_processes(
    executable: Path,
    rom_path: Path,
    rom_sha256: str,
    count: int,
    timeout: int,
) -> list[dict[str, Any]]:
    processes = [
        subprocess.Popen(
            [str(executable), str(rom_path), rom_sha256],
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
                _fail(f"mGBA runner failed ({process.returncode}): {stderr.strip()}")
            if stderr:
                _fail(f"mGBA runnerがstderrを出力しました: {stderr.strip()}")
            try:
                value = json.loads(stdout)
            except json.JSONDecodeError as error:
                _fail(f"mGBA runner出力がJSONではありません: {error}")
            if not isinstance(value, dict):
                _fail("mGBA runner JSON rootがobjectではありません")
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
    static = _static_inputs(config_path, config)
    runtime = config["runtime"]
    process_count = int(runtime["process_runs"])
    if process_count != 2:
        _fail("mGBA gateはexactly 2 independent processes必須です")
    compiler = shutil.which(str(runtime["compiler"]))
    if compiler is None:
        _fail("C compilerがありません")
    version = subprocess.run(
        [compiler, "--version"], cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if version.returncode != 0 or not version.stdout.splitlines():
        _fail("C compiler versionを取得できません")
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p02-mgba-", dir=local) as raw:
        executable = Path(raw) / "p02-evolution-smoke"
        command = [
            compiler,
            *map(str, runtime["compile_flags"]),
            str(ROOT / runtime["runner_source"]),
            "-o",
            str(executable),
            *map(str, runtime["link_flags"]),
        ]
        compiled = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=int(runtime["timeout_seconds"]),
            check=False,
        )
        if compiled.returncode != 0:
            _fail(f"mGBA runner compile failed: {compiled.stdout}{compiled.stderr}")
        if compiled.stdout or compiled.stderr:
            _fail("mGBA runner compileが予期しない出力を生成しました")
        results = _run_processes(
            executable,
            ROOT / config["inputs"]["stage64_rom"]["path"],
            config["inputs"]["stage64_rom"]["sha256"],
            process_count,
            int(runtime["timeout_seconds"]),
        )
    for result in results:
        _validate_runner_result(result, config)
    runner_result = results[0]
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "classification": "DIRECT_CALL_BOUNDED_NOT_SCHEDULER_E2E",
        "inputs": static,
        "execution": {
            "process_runs": process_count,
            "independent_processes": True,
            "identical_results": True,
            "compiler": compiler,
            "compiler_version": version.stdout.splitlines()[0],
            "compile_flags": runtime["compile_flags"],
            "link_flags": runtime["link_flags"],
            "runner_result_sha256": _sha(_stable(runner_result)),
        },
        "runtime_result": runner_result,
        "claims": {
            "exact_stage64_rom": True,
            "get_mega_species_thumb_executed": True,
            "dragon_ascent_630_selects_mega_rayquaza_1092": True,
            "historical_773_does_not_select_wish_mega": True,
            "null_moves_does_not_select_wish_mega": True,
            "scheduler_e2e": False,
            "full_evolution_acceptance": False,
        },
        "artifacts_written": [config["output"]],
    }


def _validate_published(
    evidence: Mapping[str, Any], config_path: Path, config: Mapping[str, Any], static: Mapping[str, Any],
) -> None:
    if (
        evidence.get("schema_version") != 1
        or evidence.get("task") != TASK
        or evidence.get("status") != "PASS"
        or evidence.get("classification") != "DIRECT_CALL_BOUNDED_NOT_SCHEDULER_E2E"
        or evidence.get("inputs") != static
        or evidence.get("execution", {}).get("process_runs") != 2
        or evidence.get("execution", {}).get("independent_processes") is not True
        or evidence.get("execution", {}).get("identical_results") is not True
        or evidence.get("claims", {}).get("scheduler_e2e") is not False
        or evidence.get("claims", {}).get("full_evolution_acceptance") is not False
        or evidence.get("artifacts_written") != [config["output"]]
    ):
        _fail(f"公開済みmGBA evidenceが入力と一致しません: {config_path}")
    _validate_runner_result(evidence.get("runtime_result", {}), config)
    if evidence["execution"].get("runner_result_sha256") != _sha(
        _stable(evidence["runtime_result"]),
    ):
        _fail("公開済みmGBA runner result hash不一致")
    required_claims = (
        "exact_stage64_rom",
        "get_mega_species_thumb_executed",
        "dragon_ascent_630_selects_mega_rayquaza_1092",
        "historical_773_does_not_select_wish_mega",
        "null_moves_does_not_select_wish_mega",
    )
    if any(evidence["claims"].get(key) is not True for key in required_claims):
        _fail("公開済みmGBA evidenceの必須claimがPASSではありません")


def validate_published_gate(
    config_path: Path = DEFAULT_CONFIG,
    *,
    stage63_bytes: bytes | None = None,
    stage64_bytes: bytes | None = None,
) -> dict[str, Any]:
    """fingerprint済み2-process evidenceを現在入力、またはsupplied ROMへ照合する。"""

    config = _read_json(config_path)
    static = _static_inputs(
        config_path,
        config,
        stage63_bytes=stage63_bytes,
        stage64_bytes=stage64_bytes,
    )
    evidence = _read_json(Path(config["output"]))
    _validate_published(evidence, config_path, config, static)
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
        output = Path(config["output"])
        if args.mode == "run":
            evidence = run_gate(args.config)
            _write(output, _stable(evidence))
        else:
            evidence = validate_published_gate(args.config)
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
        ModernizationP02MgbaError,
    ) as error:
        print(f"MODERNIZATION_P02_MGBA_{args.mode.upper()}=FAIL", file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 1
    print(
        f"MODERNIZATION_P02_MGBA_{args.mode.upper()}=PASS "
        f"processes={evidence['execution']['process_runs']} "
        f"dragon_ascent={evidence['runtime_result']['cases']['dragon_ascent']['result']} "
        f"historical_773={evidence['runtime_result']['cases']['historical_773']['result']} "
        f"null_moves={evidence['runtime_result']['cases']['null_moves']['result']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
