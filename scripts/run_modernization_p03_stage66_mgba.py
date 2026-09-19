#!/usr/bin/env python3
"""生成予定Stage66のP03 bulk代表consumerを独立2 mGBA processで検証する。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, NoReturn


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p03_stage66 import (  # noqa: E402
    ModernizationP03Stage66Error,
    Stage66Image,
    build_stage66_image,
    fixed_input,
    read_config,
    sha256,
    stable_json,
)


DEFAULT_CONFIG = Path("config/modernization_p03_stage66.json")
TASK = "USER-MODERNIZATION-P03-STAGE66-MGBA-GATE"


class ModernizationP03Stage66MgbaError(RuntimeError):
    """P03 Stage66 mGBA input identity、ABI、実行結果の違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP03Stage66MgbaError(message)


def _source_identity(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    if path.is_symlink() or not path.is_file():
        _fail(f"mGBA gate sourceが通常ファイルではありません: {relative}")
    raw = path.read_bytes()
    return {"path": relative, "size": len(raw), "sha256": sha256(raw)}


def _parse_symbol(raw: bytes, symbol: str, label: str) -> int:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        _fail(f"{label}がASCIIではありません: {error}")
    match = re.search(rf"(?m)^{re.escape(symbol)}:\s+([0-9A-Fa-f]{{8}})\s*$", text)
    if match is None:
        _fail(f"{label}に{symbol}がありません")
    return int(match.group(1), 16)


def _config_relative(config_path: Path) -> str:
    absolute = config_path if config_path.is_absolute() else ROOT / config_path
    try:
        return absolute.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        _fail("mGBA configはworkspace内でなければなりません")


def _static_inputs(
    config_path: Path,
    built: Stage66Image,
    *,
    supplied_stage66: bytes | None = None,
) -> dict[str, Any]:
    config = built.config
    output = built.rom
    if supplied_stage66 is not None and supplied_stage66 != output:
        _fail("supplied Stage66 bytesがgenerator結果と一致しません")
    relative_config = _config_relative(config_path)
    config_identity = _source_identity(relative_config)

    offsets_contract = config["inputs"]["battle_core_offsets"]
    offset_rows = []
    expected_level = int(config["runtime_gate"]["get_level_up_moves_by_species_symbol"], 16)
    expected_tm = int(config["runtime_gate"]["can_mon_learn_tmhm_symbol"], 16)
    for key in ("run_1_path", "run_2_path"):
        row = {
            "path": offsets_contract[key],
            "size": offsets_contract["size"],
            "sha256": offsets_contract["sha256"],
        }
        raw = fixed_input(ROOT, row, f"battle-core {key}")
        level = _parse_symbol(raw, "GetLevelUpMovesBySpecies", f"battle-core {key}")
        tm = _parse_symbol(raw, "CanMonLearnTMHM", f"battle-core {key}")
        if level != expected_level or tm != expected_tm:
            _fail(f"battle-core {key} consumer symbol address不一致")
        offset_rows.append({
            **row,
            "get_level_up_moves_by_species": f"0x{level:08X}",
            "can_mon_learn_tmhm": f"0x{tm:08X}",
        })

    runtime = config["runtime_gate"]
    source_paths = [
        relative_config,
        "tools/modernization_p03_stage66.py",
        "tools/modernization_learnsets.py",
        "tools/modernization_identity.py",
        runtime["gate_script"],
        runtime["runner_source"],
        *runtime["transitive_sources"],
    ]
    if len(source_paths) != len(set(source_paths)):
        _fail("mGBA gate source一覧が重複しています")
    sources = [_source_identity(path) for path in source_paths]

    lib = runtime["libmgba"]
    lib_path = Path(lib["path"])
    if not lib_path.is_file():
        _fail(f"固定libmGBAがありません: {lib_path}")
    lib_raw = lib_path.read_bytes()
    if sha256(lib_raw) != lib["sha256"]:
        _fail("固定libmGBA SHA-256不一致")

    parent_contract = config["inputs"]["parent_rom"]
    parent = fixed_input(ROOT, parent_contract, "Stage65 parent ROM")
    return {
        "config": config_identity,
        "stage65": {
            "path": parent_contract["path"],
            "size": len(parent),
            "sha256": sha256(parent),
        },
        "stage66": {
            "path": config["outputs"]["rom"],
            "size": len(output),
            "sha256": sha256(output),
        },
        "p03_contracts": {
            key: built.input_audit[key]
            for key in ("p03_contract", "p03_compiled_index", "p03_runtime_handoff")
        },
        "route_audit": {
            "corrected_target_count": built.route_audit["source_validation"][
                "corrected_target_count"
            ],
            "compiled_route_count": built.route_audit["source_validation"][
                "compiled_route_count"
            ],
            "materialized_routes": built.route_audit["materialization"][
                "materialized_routes"
            ],
            "materialized_route_content_sha256": built.route_audit["materialization"][
                "materialized_route_content_sha256"
            ],
        },
        "change_audit": {
            "changed_byte_count": built.change_audit["changed_byte_count"],
            "changed_span_count": built.change_audit["changed_span_count"],
            "changed_offsets_sha256": built.change_audit["changed_offsets_sha256"],
            "level_payload_sha256": built.change_audit["output_tables"][
                "level_payload_sha256"
            ],
        },
        "battle_core_fingerprint": offsets_contract["fingerprint"],
        "offsets": offset_rows,
        "sources": sources,
        "libmgba": {
            "path": lib["path"],
            "size": len(lib_raw),
            "sha256": sha256(lib_raw),
        },
    }


def _expected_samples(built: Stage66Image) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    for row in built.change_audit["representatives"]:
        expected.append({
            "role": row["role"],
            "species_id": row["species_id"],
            "level_pointer": row["level_payload_runtime_pointer"],
            "level_count": len(row["level_rows"]),
            "level_rows": [
                [value["project_move_id"], value["level"]]
                for value in row["level_rows"]
            ],
            "positive_machine_slot": row["positive_machine_slot"],
            "positive_machine_move": row["positive_machine_move"],
            "negative_machine_slot": row["negative_machine_slot"],
        })
    return expected


def _validate_runner_result(
    result: Mapping[str, Any], expected_sha: str, built: Stage66Image,
) -> None:
    if (
        result.get("schema_version") != 1
        or result.get("status") != "PASS"
        or result.get("classification") != "REAL_CONSUMER_DIRECT_CALL_BOUNDED"
        or result.get("rom_sha256") != expected_sha
        or result.get("read_only") is not True
        or result.get("payload_pc_seen") is not True
        or result.get("warnings_errors") != 0
        or result.get("scheduler_e2e") is not False
        or result.get("full_p03_acceptance") is not False
        or result.get("artifacts_written") != []
    ):
        _fail("mGBA runner top-level contract不一致")
    if result.get("roots") != {
        "level_up": "0x093A4CAC",
        "level_literal": "0x093A4CAC",
        "tm_compatibility": "0x0944BD00",
        "tm_catalog": "0x0944BB80",
    }:
        _fail("mGBA runner resolved root不一致")
    if result.get("symbols") != {
        "level_up": "0x091142A0",
        "level_up_thumb": "0x091142A1",
        "machine": "0x09110184",
        "machine_thumb": "0x09110185",
    }:
        _fail("mGBA runner consumer symbol不一致")
    samples = result.get("samples")
    expected = _expected_samples(built)
    if not isinstance(samples, list) or len(samples) != len(expected):
        _fail("mGBA runner representative sample件数不一致")
    for actual, wanted in zip(samples, expected, strict=True):
        for key, value in wanted.items():
            if actual.get(key) != value:
                _fail(f"mGBA sample {wanted['role']} {key}不一致")
        if actual.get("positive_result") != 1 or actual.get("negative_result") != 0:
            _fail(f"mGBA sample {wanted['role']} machine result不一致")
        for key in (
            "level_instructions",
            "positive_instructions",
            "negative_instructions",
        ):
            if not isinstance(actual.get(key), int) or actual[key] <= 0:
                _fail(f"mGBA sample {wanted['role']} {key}不一致")
        allowed = set(wanted) | {
            "positive_result",
            "negative_result",
            "level_instructions",
            "positive_instructions",
            "negative_instructions",
        }
        if set(actual) != allowed:
            _fail(f"mGBA sample {wanted['role']} field集合不一致")


def _run_processes(
    executable: Path, rom_path: Path, rom_sha: str, count: int, timeout: int,
) -> list[dict[str, Any]]:
    processes = [
        subprocess.Popen(
            [str(executable), str(rom_path), rom_sha],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(count)
    ]
    if len({process.pid for process in processes}) != count:
        for process in processes:
            process.kill()
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
    built = build_stage66_image(ROOT, config_path)
    config = built.config
    static = _static_inputs(config_path, built)
    runtime = config["runtime_gate"]
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
    with tempfile.TemporaryDirectory(prefix="p03-stage66-mgba-", dir=local) as raw:
        temporary = Path(raw)
        executable = temporary / "p03-stage66-smoke"
        rom_path = temporary / "stage66.gba"
        rom_path.write_bytes(built.rom)
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
            rom_path,
            sha256(built.rom),
            process_count,
            int(runtime["timeout_seconds"]),
        )
    for result in results:
        _validate_runner_result(result, sha256(built.rom), built)
    runner_result = results[0]
    return {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "classification": "REAL_CONSUMER_DIRECT_CALL_BOUNDED_NOT_SCHEDULER_E2E",
        "inputs": static,
        "execution": {
            "process_runs": process_count,
            "independent_processes": True,
            "identical_results": True,
            "compiler": compiler,
            "compiler_version": version.stdout.splitlines()[0],
            "compile_flags": runtime["compile_flags"],
            "link_flags": runtime["link_flags"],
            "runner_result_sha256": sha256(stable_json(runner_result)),
        },
        "runtime_result": runner_result,
        "claims": {
            "exact_generated_stage66_rom": True,
            "get_level_up_moves_by_species_executed": True,
            "can_mon_learn_tmhm_executed": True,
            "first_middle_last_and_caterpie_exercised": True,
            "replacement_not_union": True,
            "scheduler_e2e": False,
            "full_p03_acceptance": False,
        },
        "task_completion": "CHECKPOINT_NOT_P03_DONE",
        "artifacts_written": [config["outputs"]["mgba_evidence"]],
    }


def _validate_published(
    evidence: Mapping[str, Any],
    expected_inputs: Mapping[str, Any],
    expected_sha: str,
    built: Stage66Image,
) -> None:
    if (
        evidence.get("schema_version") != 1
        or evidence.get("task") != TASK
        or evidence.get("status") != "PASS"
        or evidence.get("classification")
        != "REAL_CONSUMER_DIRECT_CALL_BOUNDED_NOT_SCHEDULER_E2E"
        or evidence.get("inputs") != expected_inputs
        or evidence.get("task_completion") != "CHECKPOINT_NOT_P03_DONE"
    ):
        _fail("公開済みP03 Stage66 mGBA evidence identity不一致")
    result = evidence.get("runtime_result", {})
    _validate_runner_result(result, expected_sha, built)
    execution = evidence.get("execution", {})
    if (
        execution.get("process_runs") != 2
        or execution.get("independent_processes") is not True
        or execution.get("identical_results") is not True
        or execution.get("runner_result_sha256") != sha256(stable_json(result))
    ):
        _fail("公開済みP03 Stage66 mGBA 2-process binding不一致")
    claims = evidence.get("claims", {})
    required_true = (
        "exact_generated_stage66_rom",
        "get_level_up_moves_by_species_executed",
        "can_mon_learn_tmhm_executed",
        "first_middle_last_and_caterpie_exercised",
        "replacement_not_union",
    )
    if any(claims.get(key) is not True for key in required_true) \
            or claims.get("scheduler_e2e") is not False \
            or claims.get("full_p03_acceptance") is not False:
        _fail("公開済みP03 Stage66 mGBA claim境界不一致")


def validate_published_gate(
    config_path: Path = DEFAULT_CONFIG,
    *,
    stage66_bytes: bytes | None = None,
    built: Stage66Image | None = None,
) -> dict[str, Any]:
    resolved = built if built is not None else build_stage66_image(ROOT, config_path)
    if stage66_bytes is not None and stage66_bytes != resolved.rom:
        _fail("supplied Stage66 bytesがgenerator結果と一致しません")
    expected_inputs = _static_inputs(
        config_path, resolved, supplied_stage66=stage66_bytes,
    )
    evidence_path = ROOT / resolved.config["outputs"]["mgba_evidence"]
    if evidence_path.is_symlink() or not evidence_path.is_file():
        _fail(f"公開済みP03 Stage66 mGBA evidenceがありません: {evidence_path}")
    raw = evidence_path.read_bytes()
    try:
        evidence = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"公開済みP03 Stage66 mGBA evidenceがJSONではありません: {error}")
    if not isinstance(evidence, dict) or raw != stable_json(evidence):
        _fail("公開済みP03 Stage66 mGBA evidenceが決定的JSONではありません")
    _validate_published(evidence, expected_inputs, sha256(resolved.rom), resolved)
    return evidence


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=f".{path.name}.", delete=False,
    ) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "check"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        if args.mode == "run":
            result = run_gate(args.config)
            config = read_config(ROOT, args.config)
            _write(ROOT / config["outputs"]["mgba_evidence"], stable_json(result))
        else:
            result = validate_published_gate(args.config)
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
        ModernizationP03Stage66Error,
        ModernizationP03Stage66MgbaError,
    ) as error:
        print(f"MODERNIZATION_P03_STAGE66_MGBA_{args.mode.upper()}=FAIL", file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 1
    print(
        f"MODERNIZATION_P03_STAGE66_MGBA_{args.mode.upper()}=PASS "
        f"rom={result['runtime_result']['rom_sha256']} processes=2 "
        "samples=4 consumers=2 completion=CHECKPOINT_NOT_P03_DONE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
