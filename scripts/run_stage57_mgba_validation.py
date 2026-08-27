#!/usr/bin/env python3
"""Stage57のdomain選択式・exact-ROM高速mGBA検証を実行する。"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_species_surface import run_species_runtime_smoke  # noqa: E402
from scripts.build_world_runtime_e2e_repair import _world_input_e2e  # noqa: E402
from tools.stage57_debug_suite import full_audit, quick_audit  # noqa: E402
from tools.stage57_story_trainer_audit import audit_story_trainers  # noqa: E402


TASK = "USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR"
STAGE = 57
DEFAULT_ROM = Path("build/stages/57_comprehensive_debug_repair.gba")
DEFAULT_METADATA = Path("build/stages/57_comprehensive_debug_repair.json")
DEFAULT_OUTPUT = Path("build/stages/57_mgba_comprehensive_debug.json")
COLLECTION_SYMBOLS = Path("generated/runtime/collection_supply_v1_symbols.json")
STAGE57_SYMBOLS = Path("generated/runtime/stage57_comprehensive_debug_repair_symbols.json")
COLLECTION_CASES = Path("generated/runtime/collection_supply_v1_mgba_cases.json")
ALL_DOMAINS = (
    "static", "story", "menu", "route505", "species", "collection", "world",
)


class Stage57MgbaError(RuntimeError):
    """exact-ROM/domain/runner契約違反。"""


def _fail(message: str) -> NoReturn:
    raise Stage57MgbaError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, indent=2,
    ) + "\n"


def _without_timing(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_timing(item)
            for key, item in value.items() if key != "elapsed_seconds"
        }
    if isinstance(value, list):
        return [_without_timing(item) for item in value]
    return value


def _read_identity(
    rom_path: Path, metadata_path: Path,
) -> tuple[bytes, dict[str, Any], str]:
    raw = rom_path.read_bytes()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    digest = _sha(raw)
    if len(raw) != 32 * 1024 * 1024:
        _fail(f"Stage57 ROM size不一致: {len(raw)}")
    if (metadata.get("task"), metadata.get("stage")) != (TASK, STAGE):
        _fail("Stage57 metadata task/stage不一致")
    if metadata.get("output", {}).get("sha256") != digest:
        _fail("Stage57 ROM/metadata SHA-256不一致")
    return raw, metadata, digest


def _compile(source: Path, executable: Path) -> None:
    compiler = shutil.which("cc")
    if compiler is None or not source.is_file():
        _fail(f"mGBA compile前提不足: {source}")
    completed = subprocess.run(
        [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
         "-pedantic", str(source), "-o", str(executable), "-lmgba"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=120, check=False,
    )
    if completed.returncode or completed.stdout or completed.stderr:
        _fail(
            f"mGBA runner compile失敗 {source.name}: "
            + (completed.stderr or completed.stdout or str(completed.returncode))[-4000:]
        )


def _run_json(
    command: Sequence[str], *, cwd: Path, timeout: int, label: str,
) -> dict[str, Any]:
    completed = subprocess.run(
        list(command), cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=False,
    )
    if completed.returncode or completed.stderr:
        _fail(
            f"{label}失敗 exit={completed.returncode}: "
            + (completed.stderr or completed.stdout or str(completed.returncode))[-6000:]
        )
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        _fail(f"{label} JSON不正: {error}")
    if not isinstance(document, dict) or document.get("status") != "PASS":
        _fail(f"{label} PASS契約不一致: {document}")
    return _without_timing(document)


def _repeat(
    runs: int,
    runner: Callable[[int], dict[str, Any]],
    label: str,
) -> dict[str, Any]:
    documents = [runner(index) for index in range(runs)]
    if any(document != documents[0] for document in documents[1:]):
        _fail(f"{label}の独立{runs} process結果が非決定的です")
    return {
        "status": "PASS",
        "process_runs": runs,
        "identical_results": True,
        "result": documents[0],
    }


def _validate_result_rom(document: Mapping[str, Any], digest: str, label: str) -> None:
    value = document.get("rom_sha256")
    if value is not None and value != digest:
        _fail(f"{label} ROM SHA-256不一致: {value}")


def _static_domain(
    raw: bytes, metadata: Mapping[str, Any], digest: str, full: bool,
) -> dict[str, Any]:
    audit = full_audit if full else quick_audit
    result = _without_timing(audit(raw, metadata=metadata))
    repeated = _without_timing(audit(raw, metadata=metadata))
    _validate_result_rom(result, digest, "static")
    if result != repeated:
        _fail("static audit反復結果が非決定的です")
    return {
        "status": "PASS", "process_runs": 2,
        "identical_results": True, "mode": "full" if full else "quick",
        "result": result,
    }


def _story_domain(raw: bytes, digest: str) -> dict[str, Any]:
    first = _without_timing(audit_story_trainers(
        raw, expected_rom_sha256=digest,
    ))
    second = _without_timing(audit_story_trainers(
        raw, expected_rom_sha256=digest,
    ))
    if first != second:
        _fail("story audit反復結果が非決定的です")
    return {
        "status": "PASS", "process_runs": 2,
        "identical_results": True, "result": first,
    }


def _menu_domain(
    rom: Path, digest: str, directory: Path, runs: int,
) -> dict[str, Any]:
    source = ROOT / "tools/mgba_stage57_menu_smoke.c"
    executable = directory / "menu-runner"
    _compile(source, executable)

    def run(index: int) -> dict[str, Any]:
        work = directory / f"menu-{index + 1}"
        document = _run_json(
            [str(executable), str(rom), str(work)], cwd=ROOT, timeout=900,
            label=f"menu process {index + 1}",
        )
        _validate_result_rom(document, digest, "menu")
        return document

    return _repeat(runs, run, "menu")


def _route505_domain(
    rom: Path, digest: str, directory: Path, runs: int,
) -> dict[str, Any]:
    source = ROOT / "tools/mgba_stage57_route505_smoke.c"
    executable = directory / "route505-runner"
    _compile(source, executable)

    def run(index: int) -> dict[str, Any]:
        work = directory / f"route505-{index + 1}"
        work.mkdir()
        document = _run_json(
            [str(executable), str(rom), digest, str(work)],
            cwd=ROOT, timeout=1800, label=f"Route505 process {index + 1}",
        )
        _validate_result_rom(document, digest, "Route505")
        return document

    return _repeat(runs, run, "Route505")


def _species_domain(raw: bytes, digest: str, runs: int) -> dict[str, Any]:
    def run(_: int) -> dict[str, Any]:
        result = _without_timing(run_species_runtime_smoke(ROOT, raw))
        result.pop("process_runs", None)
        return result

    result = _repeat(runs, run, "Species")
    result["rom_sha256"] = digest
    return result


def _collection_domain(
    rom: Path, digest: str, directory: Path, runs: int, mode: str,
) -> dict[str, Any]:
    source = ROOT / "tools/mgba_stage57_collection_smoke.c"
    executable = directory / "collection-runner"
    _compile(source, executable)

    def run(index: int) -> dict[str, Any]:
        document = _run_json(
            [str(executable), str(rom), str(ROOT / COLLECTION_SYMBOLS),
             str(ROOT / STAGE57_SYMBOLS), str(ROOT / COLLECTION_CASES), mode,
             str(directory / f"collection-{index + 1}.sav")],
            cwd=ROOT, timeout=1800,
            label=f"Collection {mode} process {index + 1}",
        )
        _validate_result_rom(document, digest, "Collection")
        if document.get("warnings") != 0 or not all(
                document.get("tests", {}).values()):
            _fail("Collection test/warning契約不一致")
        return document

    result = _repeat(runs, run, f"Collection {mode}")
    result["mode"] = mode
    return result


def _world_domain(raw: bytes, digest: str) -> dict[str, Any]:
    result = _without_timing(_world_input_e2e(raw))
    if (result.get("status"), result.get("process_runs"),
            result.get("identical_results"), result.get("warnings")) \
            != ("PASS", 2, True, 0):
        _fail("world E2E契約不一致")
    return {"status": "PASS", "rom_sha256": digest, **result}


def _expand_profiles(requested: Sequence[str]) -> tuple[set[str], str]:
    selected: set[str] = set()
    profile = "custom"
    for name in requested:
        if name == "quick":
            selected.update(("static", "story"))
            if len(requested) == 1:
                profile = "quick"
        elif name == "smoke":
            selected.update(("static", "story", "menu", "species", "collection"))
            if len(requested) == 1:
                profile = "smoke"
        elif name == "all":
            selected.update(ALL_DOMAINS)
            if len(requested) == 1:
                profile = "all"
        else:
            selected.add(name)
    return selected, profile


def run_validation(
    rom_path: Path,
    metadata_path: Path,
    requested: Sequence[str],
    *,
    runs: int,
    jobs: int,
    collection_mode: str,
) -> dict[str, Any]:
    raw, metadata, digest = _read_identity(rom_path, metadata_path)
    selected, profile = _expand_profiles(requested)
    if not selected:
        _fail("domainが空です")
    if runs not in (1, 2):
        _fail("runsは1または2です")
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stage57-mgba-", dir=local) as raw_dir:
        directory = Path(raw_dir)
        functions: dict[str, Callable[[], dict[str, Any]]] = {
            "static": lambda: _static_domain(
                raw, metadata, digest, profile == "all"),
            "story": lambda: _story_domain(raw, digest),
            "menu": lambda: _menu_domain(rom_path, digest, directory, runs),
            "route505": lambda: _route505_domain(
                rom_path, digest, directory, runs),
            "species": lambda: _species_domain(raw, digest, runs),
            "collection": lambda: _collection_domain(
                rom_path, digest, directory, runs, collection_mode),
            "world": lambda: _world_domain(raw, digest),
        }
        results: dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(max(1, jobs), len(selected)),
        ) as executor:
            pending = {
                executor.submit(functions[name]): name for name in sorted(selected)
            }
            for future in concurrent.futures.as_completed(pending):
                name = pending[future]
                results[name] = future.result()
    warnings = sum(
        int(result.get("result", result).get("warnings", 0))
        for result in results.values()
    )
    if warnings:
        _fail(f"mGBA warnings残存: {warnings}")
    full_coverage = set(results) == set(ALL_DOMAINS)
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "tool": "run_stage57_mgba_validation",
        "status": "PASS",
        "profile": profile,
        "rom": str(rom_path),
        "rom_sha256": digest,
        "selected_domains": sorted(results),
        "domain_count": len(results),
        "full_coverage": full_coverage,
        "dynamic_process_runs": runs,
        "warnings": 0,
        "domains": {name: results[name] for name in sorted(results)},
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument(
        "--domain", action="append",
        choices=("quick", "smoke", "all", *ALL_DOMAINS),
        default=[], help="複数指定可。未指定はquick。",
    )
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument(
        "--collection-mode", choices=("quick", "full"), default="full",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    requested = args.domain or ["quick"]
    try:
        document = run_validation(
            args.rom, args.metadata, requested, runs=args.runs,
            jobs=args.jobs, collection_mode=args.collection_mode,
        )
        output = args.output
        if output is None and document["profile"] == "all" and not args.no_write:
            output = DEFAULT_OUTPUT
        rendered = _stable(document)
        if output is not None and not args.no_write:
            output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=output.parent, delete=False, mode="w", encoding="utf-8",
            ) as stream:
                stream.write(rendered)
                temporary = Path(stream.name)
            os.replace(temporary, output)
        print(rendered, end="")
        return 0
    except (
        OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
        subprocess.SubprocessError, Stage57MgbaError,
    ) as error:
        print(f"Stage57 mGBA validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
