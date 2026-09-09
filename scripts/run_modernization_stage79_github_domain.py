#!/usr/bin/env python3
"""GitHub Actions上でStage79の各domainを並列実行し、結果を合成する。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = ROOT / "scripts/run_modernization_stage79_cumulative_mgba.py"
DEFAULT_CONFIG = Path("config/modernization_stage79_cumulative_mgba.json")


class Stage79GithubDomainError(RuntimeError):
    """Actions用のdomain実行または結果合成に失敗した。"""


def _fail(message: str) -> NoReturn:
    raise Stage79GithubDomainError(message)


def _load_orchestrator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "modernization_stage79_cumulative_mgba", ORCHESTRATOR
    )
    if spec is None or spec.loader is None:
        _fail("Stage79 orchestratorをimportできません")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _config_path(path: Path) -> Path:
    candidate = path if path.is_absolute() else ROOT / path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(ROOT.resolve(strict=True))
    except (OSError, ValueError) as error:
        _fail(f"configがworkspace外または欠落です: {error}")
    if candidate.is_symlink() or not resolved.is_file():
        _fail("configはworkspace内の通常file必須です")
    return resolved


def _read_config(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(_config_path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"configを読めません: {error}")
    if not isinstance(document, dict):
        _fail("config rootはobject必須です")
    return document


def _domain(
    module: ModuleType, config: Mapping[str, Any], domain_id: str
) -> Mapping[str, Any]:
    domains = config.get("domains")
    if not isinstance(domains, list):
        _fail("config.domainsはarray必須です")
    matches = [row for row in domains if isinstance(row, Mapping)
               and row.get("id") == domain_id]
    if len(matches) != 1:
        _fail(f"未知または重複したdomainです: {domain_id}")
    domain = matches[0]
    if domain.get("state") != module.READY:
        _fail(f"domainはREADYではありません: {domain_id}")
    return domain


def _output_directory(path: Path) -> Path:
    candidate = path if path.is_absolute() else ROOT / path
    try:
        candidate.resolve().relative_to(ROOT.resolve(strict=True))
        candidate.mkdir(parents=True, exist_ok=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(ROOT.resolve(strict=True))
    except (OSError, ValueError) as error:
        _fail(f"出力directoryがworkspace外または作成不能です: {error}")
    if candidate.is_symlink() or not resolved.is_dir():
        _fail("出力先はworkspace内の通常directory必須です")
    return resolved


def _read_record(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file():
            _fail(f"resultが通常fileではありません: {path}")
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"resultを読めません: {path}: {error}")
    if not isinstance(record, dict):
        _fail(f"result rootはobject必須です: {path}")
    return record


def _context(
    module: ModuleType, config_path: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    plan = module.build_plan(config_path)
    config = _read_config(config_path)
    input_rom = module._identity(plan["input"]["rom"]["path"], "cumulative ROM")
    return plan, config, input_rom


def plan(config_path: Path, selection: str) -> dict[str, Any]:
    module = _load_orchestrator()
    stage79_plan, config, _input_rom = _context(module, config_path)
    order = stage79_plan["domain_order"]
    if selection != "all" and selection not in order:
        _fail(f"selectionが不正です: {selection}")
    for domain_id in order:
        _domain(module, config, domain_id)
    return {
        "schema_version": 1,
        "task": module.TASK,
        "stage": module.STAGE,
        "status": "GITHUB_MATRIX_READY",
        "selection": selection,
        "plan_fingerprint": stage79_plan["plan_fingerprint"],
        "domain_order": order,
        "input_rom": stage79_plan["input"]["rom"],
        "mGBA_process_runs": 0,
    }


def validate_domain(
    config_path: Path, domain_id: str, record_path: Path
) -> dict[str, Any]:
    module = _load_orchestrator()
    stage79_plan, config, input_rom = _context(module, config_path)
    domain = _domain(module, config, domain_id)
    record = _read_record(record_path)
    module._validate_result_record(
        domain,
        record,
        stage79_plan["plan_fingerprint"],
        input_rom,
        input_rom["sha256"],
    )
    return {
        "schema_version": 1,
        "task": module.TASK,
        "stage": module.STAGE,
        "status": "DOMAIN_RESULT_VALID",
        "id": domain_id,
        "plan_fingerprint": stage79_plan["plan_fingerprint"],
        "mGBA_process_runs": 0,
    }


def run_domain(
    config_path: Path, domain_id: str, output_path: Path
) -> dict[str, Any]:
    module = _load_orchestrator()
    stage79_plan, config, input_rom = _context(module, config_path)
    domain = _domain(module, config, domain_id)
    output = _output_directory(output_path)
    source_rom = ROOT / input_rom["path"]
    local = _output_directory(ROOT / ".local")
    with tempfile.TemporaryDirectory(
        prefix=f"stage79-{domain_id}-", dir=local
    ) as raw:
        work = Path(raw)
        private_rom = work / "stage78-private.gba"
        module._atomic_write(private_rom, source_rom.read_bytes())
        private_rom.chmod(0o444)
        executable = work / "runner"
        compilation = module._compile(domain, executable)
        command = module._command(
            domain, executable, private_rom, input_rom["sha256"], work, config
        )
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=module._integer(
                    domain["timeout_seconds"], f"{domain_id} timeout"
                ),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            _fail(f"{domain_id} mGBA実行失敗: {error}")
        module._atomic_write(
            output / "runner.stdout.json", completed.stdout.encode("utf-8")
        )
        module._atomic_write(
            output / "runner.stderr.log", completed.stderr.encode("utf-8")
        )
        source_after = module._identity(input_rom["path"], "cumulative ROM")
        private_after = {
            "size": private_rom.stat().st_size,
            "sha256": module._sha(private_rom.read_bytes()),
        }
    if source_after != input_rom \
            or private_after != {
                "size": input_rom["size"], "sha256": input_rom["sha256"]
            }:
        _fail(f"{domain_id} 実行でROM identityが変化しました")
    private_rom.chmod(0o600)
    private_rom.unlink()
    if completed.returncode != 0:
        _fail(f"{domain_id} mGBA失敗({completed.returncode})")
    try:
        runner_result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        _fail(f"{domain_id} stdout JSON不一致: {error}")
    if not isinstance(runner_result, dict):
        _fail(f"{domain_id} stdout rootがobjectではありません")
    module._validate_result(domain, runner_result, input_rom["sha256"])
    record = {
        "schema_version": 1,
        "task": module.TASK,
        "stage": module.STAGE,
        "id": domain_id,
        "status": "PASS",
        "plan_fingerprint": stage79_plan["plan_fingerprint"],
        "input_rom": input_rom,
        "runner": dict(domain["runner"]),
        "compilation": compilation,
        "command_argument_count": len(command),
        "stderr_sha256": module._sha(completed.stderr.encode("utf-8")),
        "runner_result": runner_result,
    }
    module._validate_result_record(
        domain,
        record,
        stage79_plan["plan_fingerprint"],
        input_rom,
        input_rom["sha256"],
    )
    module._atomic_write(output / "result.json", module._stable(record))
    return {
        "schema_version": 1,
        "task": module.TASK,
        "stage": module.STAGE,
        "status": "DOMAIN_PASS",
        "id": domain_id,
        "plan_fingerprint": stage79_plan["plan_fingerprint"],
        "mGBA_process_runs": 1,
        "result": (output / "result.json").relative_to(ROOT).as_posix(),
    }


def merge(
    config_path: Path, input_path: Path, output_path: Path
) -> dict[str, Any]:
    module = _load_orchestrator()
    stage79_plan, config, input_rom = _context(module, config_path)
    source = input_path if input_path.is_absolute() else ROOT / input_path
    output = _output_directory(output_path)
    if source.is_symlink() or not source.is_dir():
        _fail("merge入力は通常directory必須です")
    records: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(source.rglob("result.json")):
        record = _read_record(path)
        domain_id = record.get("id")
        if not isinstance(domain_id, str) or domain_id in records:
            _fail(f"result idが不正または重複です: {domain_id!r}")
        records[domain_id] = (path, record)
    order = stage79_plan["domain_order"]
    if set(records) != set(order):
        missing = sorted(set(order) - set(records))
        extra = sorted(set(records) - set(order))
        _fail(f"domain result集合不一致: missing={missing}, extra={extra}")

    state = module._state_directory(config, stage79_plan["plan_fingerprint"])
    state.mkdir(parents=True, exist_ok=True)
    state = module._ensure_state_subdirectory(state, state, "resume state directory")
    results_directory = module._ensure_state_subdirectory(
        state / "results", state, "resume results directory"
    )
    for domain_id in order:
        domain = _domain(module, config, domain_id)
        _path, record = records[domain_id]
        module._validate_result_record(
            domain,
            record,
            stage79_plan["plan_fingerprint"],
            input_rom,
            input_rom["sha256"],
        )
        module._atomic_write(
            results_directory / f"{domain_id}.json", module._stable(record)
        )
    checkpoint = {
        "schema_version": 1,
        "task": module.TASK,
        "stage": module.STAGE,
        "status": "IN_PROGRESS",
        "plan_fingerprint": stage79_plan["plan_fingerprint"],
        "input": stage79_plan["input"],
        "domain_order": order,
        "domains": {domain_id: "PASS" for domain_id in order},
    }
    module._atomic_write(state / "checkpoint.json", module._stable(checkpoint))
    gate = module.run(config_path, heavy_confirmed=True)
    checked = module.check(config_path)
    if gate.get("status") != "PASS_WITH_DECLARED_LIMITS" \
            or checked.get("status") != "CHECK_PASS" \
            or gate.get("execution", {}).get("fresh_mGBA_process_runs") != 0 \
            or gate.get("execution", {}).get("cached_domain_results_reused") \
                != len(order):
        _fail("cached domain結果からのStage79 gate合成に失敗しました")
    gate_path = ROOT / config["execution"]["runtime_gate"]
    module._atomic_write(output / "runtime_gate.json", gate_path.read_bytes())
    module._atomic_write(output / "check.json", module._stable(checked))
    return {
        "schema_version": 1,
        "task": module.TASK,
        "stage": module.STAGE,
        "status": "GITHUB_MATRIX_MERGE_PASS",
        "plan_fingerprint": stage79_plan["plan_fingerprint"],
        "domain_order": order,
        "matrix_mGBA_process_runs": len(order),
        "merge_mGBA_process_runs": 0,
        "runtime_gate": (output / "runtime_gate.json").relative_to(ROOT).as_posix(),
        "check": (output / "check.json").relative_to(ROOT).as_posix(),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--selection", default="all")

    validate_parser = subparsers.add_parser("validate-domain")
    validate_parser.add_argument("--domain", required=True)
    validate_parser.add_argument("--record", type=Path, required=True)

    run_parser = subparsers.add_parser("run-domain")
    run_parser.add_argument("--domain", required=True)
    run_parser.add_argument("--output-directory", type=Path, required=True)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--input-directory", type=Path, required=True)
    merge_parser.add_argument("--output-directory", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.mode == "plan":
            result = plan(args.config, args.selection)
        elif args.mode == "validate-domain":
            result = validate_domain(args.config, args.domain, args.record)
        elif args.mode == "run-domain":
            result = run_domain(
                args.config, args.domain, args.output_directory
            )
        else:
            result = merge(
                args.config, args.input_directory, args.output_directory
            )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (Stage79GithubDomainError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
