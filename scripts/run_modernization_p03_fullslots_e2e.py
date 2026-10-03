#!/usr/bin/env python3
"""Stage81 exact-PP learning UI, save/reload and pre-repair negative controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import modernization_p03_native_pp_repair as repair

SOURCE = "tools/mgba_modernization_p03_fullslots_e2e.c"
WRAPPER = "scripts/run_modernization_p03_fullslots_e2e.py"
RECIPE = "tools/modernization_p03_native_pp_repair.py"
WORKFLOW = ".github/workflows/p03-fullslots-e2e.yml"
TEST = "tests/test_modernization_p03_fullslots_e2e.py"
EMBEDDED = "tools/mgba_modernization_p03_learning_e2e.c"
SCOPE = "P03_NATIVE_PP_FULLSLOTS_SAVE_RELOAD_REPRESENTATIVE"
SEED_SHA = "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"
MODES = ("replace-0", "replace-1", "replace-2", "replace-3", "reject", "cancel-summary", "empty", "below-level")
NEGATIVE_MODES = ("empty", "replace-0")
WITNESS_KEYS = {"dialog", "summary", "selection", "stop", "evolution_begin", "evolution_update", "field", "down_presses"}


def identity(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"regular file required: {path}")
    return repair.identity(path.read_bytes())


def strict_pairs(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(raw: bytes) -> dict:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant: {value}")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=strict_pairs,
                      parse_constant=reject_constant)


def expected_result(mode: str) -> dict:
    if mode not in MODES:
        raise ValueError("unknown mode")
    small = mode in ("empty", "below-level")
    slot = int(mode[-1]) if mode.startswith("replace-") else (2 if mode == "empty" else -1)
    before = [33, 81, 0, 0] if small else [33, 81, 45, 52]
    pp = [7, 8, 0, 0] if small else [7, 8, 9, 10]
    after, after_pp = before.copy(), pp.copy()
    if slot >= 0:
        after[slot], after_pp[slot] = 535, 20
    return {
        "schema_version": 1, "status": "PASS", "scope": SCOPE,
        "mode": mode, "rom_sha256": repair.CANDIDATE_SHA, "species": 649,
        "initial_level": 7 if mode == "below-level" else 8,
        "final_level": 8 if mode == "below-level" else 9,
        "learned_slot": slot, "canonical_bug_bite_pp": 20,
        "moves_before": before, "pp_before": pp,
        "moves_after": after, "pp_after": after_pp,
        "normal_bag_party_input": True, "scene_keys_frames_only": True,
        "evolution_cancel_input": True, "normal_save_menu": True,
        "fresh_core_normal_continue": True, "all_slots_pp_persisted": True,
        "private_rtc_trailer_reserved": True, "save_counter_delta": 1,
        "breeding_e2e": False, "full_p03_acceptance": False,
        "release_ready": False, "warnings_errors": 0,
    }


def same_typed(actual, expected) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(same_typed(a, b) for a, b in zip(actual, expected))
    return actual == expected


def validate_result(raw: bytes, mode: str, returncode: int) -> dict:
    if type(returncode) is not int or returncode != 0:
        raise ValueError(f"mGBA exit code not integer zero: {returncode!r}")
    expected = expected_result(mode)
    result = strict_json(raw)
    if type(result) is not dict or set(result) != set(expected) | {"witness"}:
        raise ValueError("result schema mismatch")
    for key, value in expected.items():
        if not same_typed(result[key], value):
            raise ValueError(f"result contract mismatch: {key}")
    w = result["witness"]
    if type(w) is not dict or set(w) != WITNESS_KEYS:
        raise ValueError("witness schema mismatch")
    if any(type(v) is not int or not 0 <= v <= 24000 for v in w.values()):
        raise ValueError("witness frame/count is not a bounded integer")
    if not 0 < w["evolution_begin"] < w["evolution_update"] < w["field"]:
        raise ValueError("evolution/return ordering missing")
    summary = mode.startswith("replace-") or mode == "cancel-summary"
    if summary:
        if not 0 < w["dialog"] < w["summary"] < w["selection"] < w["evolution_begin"]:
            raise ValueError("summary input ordering missing")
    elif mode == "reject":
        if not 0 < w["dialog"] < w["stop"] or w["summary"] or w["selection"]:
            raise ValueError("reject input ordering mismatch")
    elif any(w[k] for k in ("dialog", "summary", "selection", "stop")):
        raise ValueError("unexpected full-slot dialog")
    if mode in ("reject", "cancel-summary"):
        previous = w["selection"] if summary else w["dialog"]
        if not previous < w["stop"] < w["evolution_begin"]:
            raise ValueError("stop-learning confirmation missing")
    elif w["stop"]:
        raise ValueError("unexpected stop-learning confirmation")
    down = int(mode[-1]) if mode.startswith("replace-") else 0
    if w["down_presses"] != down:
        raise ValueError("physical cursor navigation differs")
    return result


def validate_parent_failure(stdout: bytes, stderr: bytes, returncode: int) -> None:
    if type(returncode) is not int or returncode != 1 or stdout:
        raise ValueError("pre-repair control did not fail cleanly without PASS JSON")
    if not stderr.endswith(b"move slot PP differs from canonical/retained PP\n") or b"pp=45/20\n" not in stderr:
        raise ValueError("pre-repair failure was not the reproduced PP error")
    if any(word in stderr for word in (b"mGBA[", b"scene_timeout", b"ROM changed")):
        raise ValueError("pre-repair control contains an unrelated runtime failure")


def embed(source: str, replacement: str) -> str:
    entry = "int main(int argc, char **argv)"
    if source.count(entry) != 1:
        raise ValueError("embedded entrypoint not unique")
    return source.replace(entry, f"int {replacement}(int argc, char **argv)", 1)


def capture(command: list[str], prefix: Path, timeout: int) -> tuple[bytes, bytes, dict]:
    """Always retain byte-exact partial output and process outcome, even on failure."""
    stdout, stderr = b"", b""
    process = {"schema_version": 1, "returncode": None, "timed_out": False, "spawn_error": None}
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=timeout, check=False)
        stdout, stderr = completed.stdout, completed.stderr
        process["returncode"] = completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or b"", error.stderr or b""
        process["timed_out"] = True
    except OSError as error:
        process["spawn_error"] = str(error)
    finally:
        prefix.with_suffix(".stdout").write_bytes(stdout)
        prefix.with_suffix(".stderr").write_bytes(stderr)
        prefix.with_suffix(".process.json").write_text(json.dumps(process, indent=2) + "\n")
    return stdout, stderr, process


def require_exited(process: dict) -> int:
    if process["timed_out"] is not False or process["spawn_error"] is not None:
        raise ValueError(f"process did not finish normally: {process}")
    if type(process["returncode"]) is not int:
        raise ValueError("process exit code missing or not integer")
    return process["returncode"]


def prepare_output(path: Path) -> Path:
    output = path.absolute()
    output.resolve().relative_to((ROOT / ".local").resolve())
    if output.is_symlink():
        raise ValueError("symlink output forbidden")
    output.mkdir(parents=True, exist_ok=True)
    names = ["result.json", "candidate.json"]
    for name in ("compile", *MODES, *(f"parent-{m}" for m in NEGATIVE_MODES)):
        names += [name + suffix for suffix in (".stdout", ".stderr", ".process.json")]
    for name in names:
        (output / name).unlink(missing_ok=True)
    return output


def run(output: Path) -> dict:
    output = prepare_output(output)  # Invalidate stale PASS before any input/build failure.
    cfg_path = "config/modernization_stage79_cumulative_mgba.json"
    cfg = strict_json((ROOT / cfg_path).read_bytes())
    domain = next(d for d in cfg["domains"] if d["id"] == "p02")
    seed = ROOT / domain["seed_save"]["path"]
    parent = ROOT / repair.PARENT_PATH
    expected_seed = {"size": 131072, "sha256": SEED_SHA}
    if identity(seed) != expected_seed:
        raise ValueError("fixed seed identity mismatch")
    bindings = {}
    for row in (domain["runner"], *domain["dependencies"]):
        actual = identity(ROOT / row["path"])
        if actual != {"size": row["size"], "sha256": row["sha256"]}:
            raise ValueError(f"pinned dependency mismatch: {row['path']}")
        bindings[row["path"]] = actual
    target = strict_json((ROOT / "config/modernization_p03_stage65.json").read_bytes())["target"]
    route = next(r for r in target["level_up_routes"] if r["move_key"] == "MOVE_KEY_BUGBITE")
    if (target["species_id"], route["learning_level"], route["project_move_id"]) != (649, 9, 535):
        raise ValueError("adopted learning route changed")
    for name in (SOURCE, WRAPPER, RECIPE, WORKFLOW, TEST, EMBEDDED, cfg_path,
                 "config/modernization_p03_stage65.json", "config/active_play_baseline.json",
                 "infra/toolchain_manifest.json", "infra/setup_github_actions.sh"):
        bindings[name] = identity(ROOT / name)
    original_parent = identity(parent)
    candidate, build_report = repair.build(parent.read_bytes())
    (output / "candidate.json").write_text(json.dumps(build_report, indent=2) + "\n")
    cases, controls = [], []
    try:
        with tempfile.TemporaryDirectory(prefix="p03-fullslots-", dir=ROOT / ".local") as temporary:
            work = Path(temporary)
            (work / "p03_p02_embedded.c").write_text(embed((ROOT / domain["runner"]["path"]).read_text(), "p03_existing_p02_main"))
            (work / "p03_learning_embedded.c").write_text(embed((ROOT / EMBEDDED).read_text(), "p03f_previous_main"))
            executable = work / "runner"
            command = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-Itools", f"-I{work}", SOURCE, "-lmgba", "-o", str(executable)]
            _, _, compilation = capture(command, output / "compile", 120)
            if require_exited(compilation) != 0:
                raise ValueError("strict C compilation failed")
            for mode, is_parent in [(m, True) for m in NEGATIVE_MODES] + [(m, False) for m in MODES]:
                name = f"parent-{mode}" if is_parent else mode
                rom, save = work / f"{name}.gba", work / f"{name}.srm"
                rom.write_bytes(parent.read_bytes() if is_parent else candidate)
                rom.chmod(0o444)
                shutil.copyfile(seed, save)
                expected_rom = original_parent if is_parent else build_report["candidate"]
                command = [str(executable), str(rom), str(save), expected_rom["sha256"], SEED_SHA, mode]
                try:
                    stdout, stderr, process = capture(command, output / name, 900)
                finally:
                    if identity(rom) != expected_rom or identity(parent) != original_parent or identity(seed) != expected_seed:
                        raise ValueError("ROM/seed changed during runtime")
                code = require_exited(process)
                common = {"mode": mode, "process": process,
                          "stdout": identity(output / f"{name}.stdout"),
                          "stderr": identity(output / f"{name}.stderr"),
                          "private_save_after": identity(save)}
                if is_parent:
                    validate_parent_failure(stdout, stderr, code)
                    controls.append({**common, "expected_failure": "canonical PP 20, observed 45", "rom_sha256": repair.PARENT_SHA})
                else:
                    result = validate_result(stdout, mode, code)
                    if identity(save)["size"] != 131088 or save.read_bytes()[:131072] == seed.read_bytes():
                        raise ValueError("native save did not update the private flash data")
                    cases.append({**common, "runner_result": result})
    finally:
        if identity(parent) != original_parent or identity(seed) != expected_seed:
            raise ValueError("original ROM/seed changed")
        for name, before in bindings.items():
            if identity(ROOT / name) != before:
                raise ValueError(f"source/baseline changed: {name}")
    report = {
        "schema_version": 1, "status": "PASS", "scope": SCOPE,
        "candidate_build": build_report, "source_bindings": bindings, "seed": expected_seed,
        "fresh_process_runs": 10, "accepted_candidate_runs": 8, "negative_control_runs": 2,
        "cached_results_reused": 0, "cases": cases, "pre_repair_controls": controls,
        "full_p03_acceptance": False, "breeding_e2e": False, "release_ready": False,
        "active_baseline_changed": False, "current_stage79_candidate_changed": False,
    }
    destination = output / "result.json"
    temporary_result = output / "result.json.tmp"
    temporary_result.write_text(json.dumps(report, indent=2) + "\n")
    os.replace(temporary_result, destination)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, default=ROOT / ".local/p03-fullslots-e2e")
    args = parser.parse_args()
    print(json.dumps(run(args.output_directory), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
