#!/usr/bin/env python3
"""検証済みstageを再利用し、変更所有stage以降だけで開発ROMを作る。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
STATE = Path(".local/fast_rom_state.json")
ROM_SIZE = 32 * 1024 * 1024


class FastRomError(RuntimeError):
    """差分stage連鎖または最終ROM契約が不正。"""


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...]


STEPS = (
    Step("battle-core", ("scripts/build_battle_core.py", "build")),
    Step("species", ("scripts/build_species_port.py", "build")),
    Step("save-layout", ("scripts/build_save_compatibility.py", "build")),
    Step("species-surface", ("scripts/build_species_surface.py", "build")),
    Step("engine-slice", ("scripts/build_engine_vertical_slice.py", "build")),
    Step("kanto-import", ("scripts/build_kanto_import.py", "build")),
    Step("content-schema", ("scripts/build_content_schema.py", "build")),
    Step("vermilion-slice", ("scripts/build_vermilion_slice.py", "build")),
    Step("kanto-maps", ("scripts/build_full_kanto_import.py", "build")),
    Step("kanto-progression", ("scripts/build_kanto_progression.py", "build")),
    Step("content-population", ("scripts/build_content_population.py", "build")),
    Step("regression", ("scripts/build_regression.py", "build")),
    Step("trainer-rebalance", ("scripts/build_trainer_rebalance_v4.py", "build")),
    Step("facility-runtime", ("scripts/build_facility_runtime.py", "build")),
    Step("first-battle-hotfix", ("scripts/build_first_battle_hotfix.py", "build")),
    Step("hm-field-access", ("scripts/build_hm_field_access.py", "build")),
    Step("battle-rules", ("scripts/build_battle_rules.py", "build")),
    Step("battle-ui", ("scripts/build_battle_ui.py", "build")),
    Step("move-memory", ("scripts/build_move_memory.py", "build")),
    Step("qol-release", ("scripts/build_qol_release.py", "build")),
    Step("final", ("scripts/build_release.py", "final-fast")),
)
STEP_INDEX = {step.name: index for index, step in enumerate(STEPS)}


OWNER_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("battle-core", (
        "config/battle_core.json", "config/cfru_vega_minimal.h",
        "config/ram_layout.csv",
        "overlays/cfru/", "tools/mgba_battle_core_",
        "tools/mgba_battle_policy_smoke.c", "tools/mgba_ai_fixture_runner.c",
        "scripts/build_battle_core.py", "scripts/build_upstream.py",
        "tools/engine/cfru_", "tools/engine/t06_",
    )),
    ("species", ("scripts/build_species_port.py",)),
    ("save-layout", ("scripts/build_save_compatibility.py", "overlays/save_migration/")),
    ("species-surface", ("scripts/build_species_surface.py",)),
    ("engine-slice", ("scripts/build_engine_vertical_slice.py",)),
    ("kanto-import", ("scripts/build_kanto_import.py",)),
    ("content-schema", ("scripts/build_content_schema.py",)),
    ("vermilion-slice", ("scripts/build_vermilion_slice.py",)),
    ("kanto-maps", ("scripts/build_full_kanto_import.py",)),
    ("kanto-progression", ("scripts/build_kanto_progression.py",)),
    ("content-population", ("scripts/build_content_population.py",)),
    ("regression", ("scripts/build_regression.py", "tools/mgba_regression_smoke.c")),
    ("trainer-rebalance", ("scripts/build_trainer_rebalance_v4.py",)),
    ("facility-runtime", (
        "scripts/build_facility_runtime.py", "overlays/facility_runtime/",
    )),
    ("first-battle-hotfix", (
        "scripts/build_first_battle_hotfix.py", "overlays/first_battle_hotfix/",
        "tools/mgba_first_battle_loop_smoke.c",
    )),
    ("hm-field-access", (
        "scripts/build_hm_field_access.py", "overlays/hm_field_access/",
        "tools/mgba_hm_field_access_smoke.c",
    )),
    ("battle-rules", (
        "scripts/build_battle_rules.py", "config/battle_rules.json",
        "tools/mgba_battle_rules_smoke.c",
    )),
    ("battle-ui", (
        "scripts/build_battle_ui.py", "config/battle_ui.json",
        "overlays/battle_ui/", "tools/mgba_battle_ui_smoke.c",
    )),
    ("move-memory", (
        "scripts/build_move_memory.py", "config/move_memory.json",
        "overlays/move_memory/", "tools/mgba_move_memory_smoke.c",
    )),
    ("qol-release", ("scripts/build_qol_release.py",)),
    ("final", ("scripts/build_release.py",)),
)

NON_ROM_PREFIXES = (
    "design/", "tasks/", "docs/", "reports/", ".github/",
    "tests/",
    "README", "CHANGELOG", "CREDITS", "KNOWN_ISSUES", "AGENTS.md",
    "scripts/build_fast_rom.py", "scripts/fast_stage_reuse.py", "Makefile",
)


def _fail(message: str) -> NoReturn:
    raise FastRomError(message)


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_files() -> list[str]:
    completed = subprocess.run(
        ("git", "ls-files", "--cached", "--others", "--exclude-standard"),
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        _fail("git ls-files failed: " + completed.stderr.strip())
    return sorted(path for path in completed.stdout.splitlines() if path)


def tracked_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in _git_files():
        path = ROOT / relative
        if path.is_file() and not path.is_symlink():
            result[relative] = _sha_file(path)
    return result


def _read_previous_hashes() -> dict[str, str] | None:
    path = ROOT / STATE
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    hashes = value.get("tracked_inputs") if isinstance(value, dict) else None
    if not isinstance(hashes, dict) or not all(
        isinstance(key, str) and isinstance(digest, str)
        for key, digest in hashes.items()
    ):
        _fail("fast ROM state is malformed")
    return hashes


def changed_files(current: dict[str, str]) -> list[str]:
    previous = _read_previous_hashes()
    if previous is not None:
        return sorted(
            path for path in set(previous) | set(current)
            if previous.get(path) != current.get(path)
        )
    completed = subprocess.run(
        ("git", "status", "--porcelain", "--untracked-files=all"),
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if completed.returncode:
        _fail("git status failed: " + completed.stderr.strip())
    result = []
    for line in completed.stdout.splitlines():
        if len(line) >= 4:
            result.append(line[3:].split(" -> ")[-1])
    return sorted(set(result))


def owner_for_path(path: str) -> str | None:
    if path.startswith(NON_ROM_PREFIXES):
        return None
    for owner, patterns in OWNER_RULES:
        if any(path == pattern or path.startswith(pattern) for pattern in patterns):
            return owner
    return "battle-core"


def choose_start(paths: Sequence[str]) -> str:
    owners = [owner_for_path(path) for path in paths]
    owners = [owner for owner in owners if owner is not None]
    return min(owners, key=STEP_INDEX.__getitem__) if owners else "final"


def _prerequisite(start: str) -> Path:
    prerequisites = {
        "battle-core": Path("build/stages/04_moves.gba"),
        "species": Path("build/stages/06_battle_core.gba"),
        "save-layout": Path("build/stages/07_species.gba"),
        "species-surface": Path("build/stages/07_species.gba"),
        "engine-slice": Path("build/stages/09_species_surface.gba"),
        "kanto-import": Path("build/stages/09_species_surface.gba"),
        "content-schema": Path("manifests/kanto_maps.csv"),
        "vermilion-slice": Path("generated/content/dry_run.json"),
        "kanto-maps": Path("generated/kanto/vermilion/bindings.json"),
        "kanto-progression": Path("content/kanto_map_scope.csv"),
        "content-population": Path("generated/kanto/progression/graph.json"),
        "regression": Path("build/stages/16_content.gba"),
        "trainer-rebalance": Path("build/stages/17_regression.gba"),
        "facility-runtime": Path("build/stages/19_trainer_rebalance.gba"),
        "first-battle-hotfix": Path("build/stages/20_facility_runtime.gba"),
        "hm-field-access": Path("build/stages/21_first_battle_hotfix.gba"),
        "battle-rules": Path("build/stages/22_hm_field_access.gba"),
        "battle-ui": Path("build/stages/23_battle_rules.gba"),
        "move-memory": Path("build/stages/24_battle_ui.gba"),
        "qol-release": Path("build/stages/25_move_memory.gba"),
        "final": Path("build/stages/25_move_memory.gba"),
    }
    return prerequisites[start]


def _run_step(step: Step, environment: dict[str, str]) -> float:
    started = time.monotonic()
    print(f"FAST_ROM STEP={step.name} STATUS=START", flush=True)
    completed = subprocess.run(
        (sys.executable, *step.command), cwd=ROOT, env=environment, check=False,
    )
    elapsed = time.monotonic() - started
    if completed.returncode:
        _fail(f"step failed: {step.name} ({completed.returncode})")
    print(f"FAST_ROM STEP={step.name} STATUS=PASS SECONDS={elapsed:.1f}", flush=True)
    return elapsed


def _final_rom() -> Path:
    candidates = sorted((ROOT / "build/final").glob("vega-modern-kanto-v*.gba"))
    if not candidates:
        _fail("final ROM was not published")
    return max(candidates, key=lambda path: path.stat().st_mtime_ns)


def build(start: str, paths: Sequence[str], hashes: dict[str, str]) -> dict[str, object]:
    prerequisite = ROOT / _prerequisite(start)
    if not prerequisite.is_file() or prerequisite.is_symlink():
        _fail(f"validated prerequisite is missing: {prerequisite.relative_to(ROOT)}")
    if prerequisite.suffix == ".gba" and prerequisite.stat().st_size not in {
        16 * 1024 * 1024, ROM_SIZE,
    }:
        _fail(f"validated prerequisite ROM size differs: {prerequisite.relative_to(ROOT)}")
    start_index = STEP_INDEX[start]
    environment = dict(os.environ)
    environment["VEGA_FAST_STAGE_REUSE"] = "1"
    reused = [step.name for step in STEPS[:start_index]]
    print(
        f"FAST_ROM START={start} REUSED={','.join(reused) or '-'} "
        f"CHANGED={','.join(paths) or '-'}",
        flush=True,
    )
    timings: dict[str, float] = {}
    total_started = time.monotonic()
    for step in STEPS[start_index:]:
        timings[step.name] = _run_step(step, environment)
    elapsed = time.monotonic() - total_started
    final = _final_rom()
    if final.stat().st_size != ROM_SIZE:
        _fail("fast final ROM size differs")
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "PASS",
        "start": start,
        "reused_steps": reused,
        "executed_steps": list(timings),
        "timings_seconds": timings,
        "elapsed_seconds": round(elapsed, 3),
        "changed_files": list(paths),
        "final_rom": final.relative_to(ROOT).as_posix(),
        "final_sha256": _sha_file(final),
        "tracked_inputs": hashes,
    }
    state = ROOT / STATE
    state.parent.mkdir(parents=True, exist_ok=True)
    temporary = state.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(state)
    print(
        f"FAST_ROM STATUS=PASS START={start} SECONDS={elapsed:.1f} "
        f"ROM={result['final_rom']} SHA256={result['final_sha256']}",
        flush=True,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from", dest="start", default="auto", choices=("auto", *STEP_INDEX),
        help="autoは前回成功時のtracked hashから最初の変更所有stageを選ぶ",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        hashes = tracked_hashes()
        paths = changed_files(hashes)
        start = choose_start(paths) if args.start == "auto" else args.start
        if args.dry_run:
            print(json.dumps({
                "start": start,
                "changed_files": paths,
                "reused_steps": [step.name for step in STEPS[:STEP_INDEX[start]]],
                "executed_steps": [step.name for step in STEPS[STEP_INDEX[start]:]],
            }, ensure_ascii=False, sort_keys=True))
            return 0
        build(start, paths, hashes)
        return 0
    except (FastRomError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"fast ROM: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
