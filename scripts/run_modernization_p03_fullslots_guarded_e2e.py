#!/usr/bin/env python3
"""P03満杯UI/空き枠・保存・新規coreとPP境界修正を独立候補で検証。"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.run_modernization_p03_learning_e2e import SEED_SHA, embed_p02, identity
from tools.modernization_p03_native_pp_repair import (
    CANDIDATE_SHA, PARENT_PATH, PARENT_SHA, ROM_SIZE, identity as byte_identity, build as repair,
)

SCOPE = "P03_FULLSLOTS_GUARDED_UI_SAVE_RELOAD_REPRESENTATIVE"
SOURCE = "tools/mgba_modernization_p03_fullslots_guarded_e2e.c"
SEED_PATH = ".local/60_wild_species_root_repair.srm"
RTC_TRAILER = bytes(7) + b"\x40" + bytes(8)
PRIVATE_SHA = "2ee9436a43e64225ec7940e29057f8dee423f00345a41ea5cd833c449841cd13"
MODES = tuple(f"replace-{i}" for i in range(4)) + (
    "refuse", "cancel-selection", "below-level", "empty-learn", "empty-below-level",
)
CONTROLS = ("replace-0", "empty-learn")
GUARDS = ("bus8", "bus16", "bus32", "raw8", "raw16", "raw32", "register")
OWN_SOURCES = (
    SOURCE, "scripts/run_modernization_p03_fullslots_guarded_e2e.py",
    "tools/modernization_p03_native_pp_repair.py",
    "tests/test_modernization_p03_fullslots_guarded_e2e.py",
    "tools/mgba_modernization_p03_learning_e2e.c",
    "scripts/run_modernization_p03_learning_e2e.py",
    "config/modernization_stage79_cumulative_mgba.json",
    "config/modernization_p03_stage65.json", "config/active_play_baseline.json",
    ".github/workflows/p03-fullslots-guarded-e2e.yml",
    "infra/toolchain_manifest.json", "infra/setup_github_actions.sh",
)


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(raw: bytes) -> object:
    return json.loads(raw, object_pairs_hook=_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def require_exact(actual: object, expected: object, label: str = "result") -> None:
    if type(actual) is not type(expected):
        raise ValueError(f"type differs: {label}")
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError(f"keys differ: {label}")
        for key in expected:
            require_exact(actual[key], expected[key], f"{label}.{key}")
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f"length differs: {label}")
        for i, value in enumerate(expected):
            require_exact(actual[i], value, f"{label}[{i}]")
    elif actual != expected:
        raise ValueError(f"value differs: {label}")


def expected_slots(mode: str, rom_sha: str) -> tuple[list[int], list[int], list[int], list[int]]:
    if mode not in MODES or rom_sha not in (PARENT_SHA, CANDIDATE_SHA):
        raise ValueError("unknown mode/ROM")
    moves, pp = [33, 81, 45, 52], [7, 8, 9, 10]
    if mode.startswith("empty-"):
        moves[2:], pp[2:] = [0, 0], [0, 0]
    after, after_pp = moves.copy(), pp.copy()
    slot = int(mode[-1]) if mode.startswith("replace-") else 2 if mode == "empty-learn" else None
    if slot is not None:
        after[slot] = 535
        after_pp[slot] = 20 if rom_sha == CANDIDATE_SHA else 45
    return moves, pp, after, after_pp


def validate_result(raw: bytes, mode: str, rom_sha: str, returncode: int) -> dict:
    require_exact(returncode, 0, "returncode")
    if rom_sha == PARENT_SHA and mode not in CONTROLS:
        raise ValueError("parent is allowed only as the two explicit defect controls")
    before, pp, after, after_pp = expected_slots(mode, rom_sha)
    result = load_json(raw)
    if not isinstance(result, dict):
        raise ValueError("object result required")
    expected = {
        "schema_version": 1, "status": "OBSERVED", "scope": SCOPE, "mode": mode,
        "rom_sha256": rom_sha, "private_save_initial_sha256": PRIVATE_SHA,
        "species": 649, "initial_level": 7 if mode.endswith("below-level") else 8,
        "final_level": 8 if mode.endswith("below-level") else 9, "canonical_move_pp": 20,
        "before_moves": before, "before_pp": pp, "after_moves": after, "after_pp": after_pp,
        "reloaded_moves": after, "reloaded_pp": after_pp,
        "host_write_guard": True, "host_write_guard_phase": "LEARNING_SCENE",
        "normal_bag_party_input": True, "normal_save_menu": True,
        "fresh_core_normal_continue": True, "breeding_e2e": False,
        "full_p03_acceptance": False, "release_ready": False, "warnings_errors": 0,
    }
    if set(result) != set(expected) | {"trace"}:
        raise ValueError("result schema differs")
    require_exact({k: result[k] for k in expected}, expected)
    trace = result["trace"]
    keys = {"frames", "down_presses", "selection_presses", "evolution_b_presses",
            "ask_frame", "summary_frame", "stop_frame", "replaced_frame",
            "begin_frame", "update_frame", "field_frame"}
    if type(trace) is not dict or set(trace) != keys:
        raise ValueError("trace schema differs")
    if any(type(v) is not int or not 0 <= v < 24000 for v in trace.values()):
        raise ValueError("invalid trace integer")
    full = mode.startswith("replace-")
    selection = full or mode == "cancel-selection"
    refusal = mode in ("refuse", "cancel-selection")
    require_exact(trace["down_presses"], int(mode[-1]) if full else 0, "down_presses")
    require_exact(trace["selection_presses"], 1 if selection else 0, "selection_presses")
    if not 1 <= trace["evolution_b_presses"] <= 200:
        raise ValueError("no physical evolution cancellation")
    for field, present in (("ask_frame", full or refusal), ("summary_frame", selection),
                           ("stop_frame", refusal), ("replaced_frame", full)):
        if (trace[field] > 0) != present:
            raise ValueError(f"wrong native UI route: {field}")
    sequence = [trace[k] for k in ("ask_frame", "summary_frame", "stop_frame", "replaced_frame",
                                   "begin_frame", "update_frame", "field_frame") if trace[k]]
    if not (0 < trace["begin_frame"] < trace["update_frame"] < trace["field_frame"] == trace["frames"]):
        raise ValueError("evolution/field trace is incomplete")
    if any(a >= b for a, b in zip(sequence, sequence[1:])):
        raise ValueError("native events are out of order")
    return result


def write_candidate(parent: Path, destination: Path) -> dict:
    """Use the existing Stage81 recipe without overwriting any candidate or input."""
    if parent.is_symlink() or not parent.is_file():
        raise ValueError("regular parent file required")
    if destination.is_symlink() or destination.exists() or parent.resolve() == destination.resolve():
        raise ValueError("new independent candidate path required")
    data = parent.read_bytes()
    candidate, report = repair(data)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(candidate)
    destination.chmod(0o444)
    if parent.read_bytes() != data:
        raise ValueError("parent ROM changed")
    return report


def prepare_private_save(seed: Path, destination: Path) -> dict:
    require_exact(identity(seed), {"size": 131072, "sha256": SEED_SHA}, "seed")
    if destination.is_symlink() or destination.exists() or destination.resolve() == seed.resolve():
        raise ValueError("independent new save path required")
    data = seed.read_bytes()
    # libmGBA 0.10.2 RTCWrite may remap flash without updating currentBank.
    # Pre-size only the private copy with its native default 16-byte RTC footer.
    # All 128 KiB of game save data remain byte-identical to the pinned seed.
    private = data + RTC_TRAILER
    require_exact(byte_identity(private), {"size": 131088, "sha256": PRIVATE_SHA}, "private fixture")
    with destination.open("xb") as stream:
        stream.write(private)
    require_exact(identity(seed), {"size": 131072, "sha256": SEED_SHA}, "seed after fixture")
    return {"seed_prefix": byte_identity(private[:131072]), "rtc_trailer_hex": RTC_TRAILER.hex(),
            "initialized": identity(destination), "game_save_bytes_changed_before_boot": 0}


def validate_guard(completed: subprocess.CompletedProcess) -> None:
    require_exact(completed.returncode, 1, "guard returncode")
    require_exact(completed.stdout, b"", "guard stdout")
    require_exact(completed.stderr, b"P03 fullslots: host write after learning barrier\n", "guard stderr")


def source_bindings() -> dict:
    cfg = load_json((ROOT / "config/modernization_stage79_cumulative_mgba.json").read_bytes())
    domain = next(d for d in cfg["domains"] if d["id"] == "p02")
    bindings = {}
    for row in [domain["runner"], *domain["dependencies"]]:
        actual = identity(ROOT / row["path"])
        require_exact(actual, {"size": row["size"], "sha256": row["sha256"]}, row["path"])
        bindings[row["path"]] = actual
    target = load_json((ROOT / "config/modernization_p03_stage65.json").read_bytes())["target"]
    route = next(r for r in target["level_up_routes"] if r["move_key"] == "MOVE_KEY_BUGBITE")
    require_exact([target["species_id"], route["learning_level"], route["project_move_id"]], [649, 9, 535], "adopted route")
    bindings.update({name: identity(ROOT / name) for name in OWN_SOURCES})
    return bindings


def embed_learning(source: str) -> str:
    entry = "int main(int argc, char **argv)"
    if source.count(entry) != 1:
        raise ValueError("previous learning entrypoint must be unique")
    return source.replace(entry, "int p03f_previous_learning_main(int argc, char **argv)", 1)


def run(output: Path) -> dict:
    output = output.absolute()
    local = (ROOT / ".local").absolute()
    output.resolve().relative_to(local.resolve())
    if ".." in output.parts or output == local or any(p.is_symlink() for p in [output, *output.parents]):
        raise ValueError("independent non-symlink .local output directory required")
    output.mkdir(parents=True, exist_ok=True)
    names = ["compile", *(f"guard-{g}" for g in GUARDS),
             *(f"parent--{m}" for m in CONTROLS), *(f"candidate--{m}" for m in MODES)]
    for name in ["result.json", "repair.json", *[n + suffix for n in names for suffix in (".stdout", ".stderr", ".process.json")]]:
        (output / name).unlink(missing_ok=True)
    bindings = source_bindings()
    parent, seed = ROOT / PARENT_PATH, ROOT / SEED_PATH
    require_exact(identity(parent), {"size": ROM_SIZE, "sha256": PARENT_SHA}, "parent")
    require_exact(identity(seed), {"size": 131072, "sha256": SEED_SHA}, "seed")
    cases, guards = [], []

    def execute(command: list[str], name: str, timeout: int) -> subprocess.CompletedProcess:
        try:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            (output / (name + ".stdout")).write_bytes(error.stdout or b"")
            (output / (name + ".stderr")).write_bytes(error.stderr or b"")
            (output / (name + ".process.json")).write_text(json.dumps({"timeout": True, "command": command}) + "\n")
            raise
        for stream in ("stdout", "stderr"):
            (output / (name + "." + stream)).write_bytes(getattr(completed, stream))
        (output / (name + ".process.json")).write_text(json.dumps({"returncode": completed.returncode, "command": command}) + "\n")
        return completed

    try:
        with tempfile.TemporaryDirectory(prefix="p03-fullslots-guarded-", dir=local) as temporary:
            work = Path(temporary)
            candidate = work / "pp-candidate.gba"
            repair_report = write_candidate(parent, candidate)
            (output / "repair.json").write_text(json.dumps(repair_report, indent=2) + "\n")
            (work / "p03_p02_embedded.c").write_text(embed_p02((ROOT / "tools/mgba_modernization_p02_stage71_acceptance_smoke.c").read_text()))
            (work / "p03f_learning_embedded.c").write_text(embed_learning((ROOT / "tools/mgba_modernization_p03_learning_e2e.c").read_text()))
            executable = work / "runner"
            compilation = execute(["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-Itools", f"-I{work}", SOURCE, "-lmgba", "-o", str(executable)], "compile", 120)
            require_exact(compilation.returncode, 0, "strict compile")
            for guard in GUARDS:
                name = "guard-" + guard
                completed = execute([str(executable), "--guard-check", guard], name, 30)
                validate_guard(completed)
                guards.append({"api": guard, "returncode": completed.returncode,
                               **{stream: identity(output / f"{name}.{stream}") for stream in ("stdout", "stderr", "process.json")}})
            for variant, modes, rom, rom_sha in (("parent", CONTROLS, parent, PARENT_SHA), ("candidate", MODES, candidate, CANDIDATE_SHA)):
                for mode in modes:
                    name = variant + "--" + mode
                    private_rom, private_save = work / (name + ".gba"), work / (name + ".srm")
                    shutil.copyfile(rom, private_rom)
                    private_rom.chmod(0o444)
                    fixture = prepare_private_save(seed, private_save)
                    try:
                        completed = execute([str(executable), str(private_rom), str(private_save), rom_sha, PRIVATE_SHA, mode], name, 900)
                    finally:
                        require_exact(identity(private_rom), {"size": ROM_SIZE, "sha256": rom_sha}, "private ROM unchanged")
                    result = validate_result(completed.stdout, mode, rom_sha, completed.returncode)
                    final_save = identity(private_save)
                    if final_save == fixture["initialized"]:
                        raise ValueError("save remained at the unplayed fixture")
                    cases.append({"variant": variant, "mode": mode, "returncode": completed.returncode,
                                  "classification": "EXPECTED_PP_DEFECT" if variant == "parent" else "PASS",
                                  "runner_result": result, "private_save_fixture": fixture, "private_save_after": final_save,
                                  **{stream: identity(output / f"{name}.{stream}") for stream in ("stdout", "stderr", "process.json")}})
                    private_rom.unlink()
                    private_save.unlink()
            require_exact(identity(candidate), {"size": ROM_SIZE, "sha256": CANDIDATE_SHA}, "candidate unchanged")
    finally:
        for name, before in bindings.items():
            require_exact(identity(ROOT / name), before, f"source unchanged: {name}")
        require_exact(identity(parent), {"size": ROM_SIZE, "sha256": PARENT_SHA}, "parent unchanged")
        require_exact(identity(seed), {"size": 131072, "sha256": SEED_SHA}, "seed unchanged")
    report = {"schema_version": 1, "status": "PASS", "scope": SCOPE,
              "source_bindings": bindings, "parent": {"size": ROM_SIZE, "sha256": PARENT_SHA},
              "candidate": {"size": ROM_SIZE, "sha256": CANDIDATE_SHA}, "seed": {"size": 131072, "sha256": SEED_SHA},
              "repair": repair_report, "fresh_process_runs": 11, "fresh_core_instances": 22,
              "candidate_cases_passed": 9, "known_parent_defects_reproduced": 2,
              "negative_guard_process_runs": 7, "cached_results_reused": 0,
              "cases": cases, "write_guards": guards, "candidate_promoted": False,
              "active_baseline_changed": False, "full_p03_acceptance": False,
              "breeding_e2e": False, "release_ready": False}
    (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, default=ROOT / ".local/p03-fullslots-guarded-e2e")
    args = parser.parse_args()
    print(json.dumps(run(args.output_directory), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
