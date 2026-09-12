#!/usr/bin/env python3
"""Revalidate the exact generic FORM native acceptance original and emit its scoped receipt.

This checkpoint performs no emulator run. It preserves the Actions ZIP from the fixed
run, verifies the exact run/artifact/source binding and raw process records, and closes
only P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL on the 635fd890 parent candidate.
Fixed-form acceptance, full P03, successor transfer and release readiness remain open.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/pr16_generic_form_checkpoint.py"
DIRECTORY = "content/modernization/pr16_generic_form_evidence"
RECEIPT = "content/modernization/pr16_generic_form_acceptance.json"
REPO = "dekaazarashi1111-web/pokemon-vega-modern"
BRANCH = "codex/modernization-followup-20260908"
CONDITION = "P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL"
RUN = 34675976411
ARTIFACT = 10292791318
ARTIFACT_NAME = "pr16-generic-form-carry-acceptance"
ARTIFACT_SIZE = 372130
ARTIFACT_SHA256 = "f5d41c58ae1be0303dd7157d08bcee77ecd5018cbbc11e4cc4d30b1a9635914b"
HEAD = "92db3605070c65206696b03f8ab6bd596ae7d729"
WORKFLOW = ".github/workflows/pr16-generic-form-carry.yml"
JOB = 103505793891
CANDIDATE = {
    "sha256": "635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e",
    "size": 33554432,
}
CASES = ("shaymin-four-slot-roundtrip", "shaymin-party-cancel")
GUARDS = ("bus8", "bus16", "bus32", "raw8", "raw16", "raw32", "register")
SOURCE_BINDINGS = (
    "scripts/pr16_generic_form_carry.py",
    "tools/mgba_pr16_generic_form_carry.c",
    "tests/test_pr16_generic_form_carry.py",
    ".github/workflows/pr16-generic-form-carry.yml",
    "scripts/pr16_p03_form_gap_inventory.py",
    "config/modernization_p03_stage73_consumers.json",
    "content/collection_supply_v1/canonical_model.json",
)
EXPECTED_STEPS = (
    "Set up job",
    "Checkout exact triggering commit",
    "Exact HEAD, pinned toolchain and unchanged Stage84 parent",
    "Download and hash-check both pinned private source archives",
    "Rebuild fixed parent and run fail-closed focused tests",
    "Actual FORM host, page navigation, party picker, carry, cancel and cold Continue",
    "Preserve exact sources and raw evidence, never ROM, save or private archive",
    "Upload original process records, screenshots and validation receipt",
    "Post Checkout exact triggering commit",
    "Complete job",
)


class CheckpointError(ValueError):
    """Raised when the preserved original or scoped claim is inconsistent."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise CheckpointError(message)


def stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load(raw: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in items:
            need(key not in out, "duplicate JSON key")
            out[key] = value
        return out

    return json.loads(
        raw,
        object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(CheckpointError(value)),
    )


def identity(raw: bytes) -> dict[str, Any]:
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def same(left: Any, right: Any) -> bool:
    return type(left) is type(right) and stable(left) == stable(right)


def fields(value: Any, expected: dict[str, Any]) -> None:
    need(type(value) is dict, "object required")
    for key, wanted in expected.items():
        need(key in value and same(value[key], wanted), "record field differs: " + key)


def read(root: Path, relative: str | Path) -> bytes:
    path = root / relative
    need(path.is_file(), "missing checkpoint input: " + str(relative))
    need(not any(item.is_symlink() for item in (path, *path.parents)), "symlink input")
    return path.read_bytes()


def archive(raw: bytes, depth: int = 0) -> dict[str, bytes]:
    need(depth <= 2, "nested archive depth")
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        entries = bundle.infolist()
        need(len(entries) < 2000, "ZIP member bound")
        need(sum(entry.file_size for entry in entries) < 30_000_000, "ZIP size bound")
        names = [entry.filename for entry in entries]
        need(len(names) == len(set(names)), "duplicate ZIP members")
        files: dict[str, bytes] = {}
        for entry in entries:
            path = Path(entry.filename)
            need(not entry.is_dir(), "directory ZIP member")
            need(not path.is_absolute() and ".." not in path.parts and "\\" not in entry.filename,
                 "unsafe ZIP path")
            need(((entry.external_attr >> 16) & 0o170000) != 0o120000, "symlink ZIP member")
            need(path.suffix.lower() not in (".gba", ".gb", ".sav", ".srm", ".ss0", ".state", ".bin"),
                 "ROM/save/binary evidence forbidden")
            files[entry.filename] = bundle.read(entry)
            if path.suffix.lower() == ".zip":
                archive(files[entry.filename], depth + 1)
        return files


def process(files: dict[str, bytes], stem: str, expected_code: int) -> dict[str, Any]:
    value = load(files[stem + ".process.json"])
    fields(value, {
        "schema_version": 1,
        "returncode": expected_code,
        "timed_out": False,
        "spawn_error": None,
    })
    return value


def metadata(value: Any) -> None:
    fields(value, {
        "run_id": RUN,
        "head_sha": HEAD,
        "head_branch": BRANCH,
        "run_attempt": 1,
        "path": WORKFLOW,
        "status": "completed",
        "conclusion": "success",
        "artifact_id": ARTIFACT,
        "artifact_name": ARTIFACT_NAME,
        "size": ARTIFACT_SIZE,
        "sha256": ARTIFACT_SHA256,
    })
    jobs = value.get("jobs")
    need(type(jobs) is list and len(jobs) == 1, "one successful native job required")
    job = jobs[0]
    fields(job, {
        "id": JOB,
        "name": "generic-form-carry",
        "run_id": RUN,
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
    })
    steps = job.get("steps")
    need(type(steps) is list and [step.get("name") for step in steps] == list(EXPECTED_STEPS),
         "native job step sequence differs")
    need(all(step.get("status") == "completed" and step.get("conclusion") == "success" for step in steps),
         "failed/skipped/pending native step")


def _validate_case(files: dict[str, bytes], aggregate: dict[str, Any], name: str) -> dict[str, Any]:
    prefix = "pr16-generic-form-carry/" + name
    process(files, prefix, 0)
    need(b"mGBA[" not in files[prefix + ".stderr"], "emulator warning in " + name)
    row = load(files[prefix + ".stdout"])
    expected_row = next(item["result"] for item in aggregate["results"] if item["name"] == name)
    need(same(row, expected_row), "aggregate/raw case mismatch: " + name)
    common = {
        "schema_version": 1,
        "status": "PASS",
        "scope": "PR16_P03_GENERIC_FORM_CARRY_PHYSICAL",
        "case": name,
        "rom_sha256": CANDIDATE["sha256"],
        "form_index": 43,
        "eligible_ordinal": 6,
        "menu_page": 1,
        "menu_cursor": 1,
        "probe_count": 7,
        "pages_scanned": 2,
        "menu_discovery": "input-only-native-menu-probe",
        "base_species": 749,
        "target_species": 900,
        "final_species": 749,
        "moves": [98, 235, 552, 33],
        "pp": [11, 3, 4, 7],
        "pp_bonuses": 229,
        "representative_route_ids": [
            "bca6fe62e4b8925d73c8238a",
            "830d0124e9ca952d41d4a7f0",
            "57e91d3ffeb04c9795a8b6a1",
        ],
        "generic_owner_rows_sha256": "66cd203079d2a6d8ef1eb0fca6b5156c7bccbc1c720786df4953311491b5592e",
        "physical_host": [1, 36, 6, 3],
        "host_index": 3,
        "host_write_barriers": 7,
        "rtc_flash_bytes_preserved": 131072,
        "test_mode": False,
        "party_byte_preserved_on_reload": True,
        "four_move_slots_preserved": True,
        "nonselected_preserved": True,
        "starting_progress_individual_map_are_fixtures": True,
        "native_acceptance_claimed_for_all_61_individual_rows": False,
        "generic_owner_representative_accepted": True,
        "release_ready": False,
        "warnings_errors": 0,
    }
    fields(row, common)
    roundtrip = name == CASES[0]
    fields(row, {
        "result": 0 if roundtrip else 20,
        "rounds": 2 if roundtrip else 1,
        "fresh_cores": 3 if roundtrip else 2,
        "automatic_saves": 2 if roundtrip else 0,
        "manual_saves": 2 if roundtrip else 1,
        "selected_party_slot": 1 if roundtrip else 6,
    })
    traces = row.get("traces")
    need(type(traces) is list and len(traces) == row["rounds"], "case trace count differs")
    need([trace["species_after"] for trace in traces] == ([900, 749] if roundtrip else [749]),
         "case species trace differs")
    for trace in traces:
        need([trace[key] for key in ("menu_page", "menu_cursor", "probe_count", "pages_scanned")] == [1, 1, 7, 2],
             "native menu witness differs")
        need(trace["interaction"] < trace["root"] < trace["service"] < trace["page"] < trace["party"],
             "native input sequence differs")
        need(trace["returned"] < trace["saved"] < trace["reloaded"], "save/Continue sequence differs")
    return row


def _validate_diagnostics(files: dict[str, bytes], aggregate: dict[str, Any]) -> dict[str, Any]:
    report = load(files["pr16-generic-form-carry/entry-diagnostic.json"])
    fields(report, {
        "schema_version": 1,
        "status": "PASS_DIAGNOSTIC_ONLY",
        "scope": "PR16_P03_GENERIC_FORM_ENTRY_DIAGNOSTIC",
        "candidate": CANDIDATE,
        "failures": [],
        "actual_new_processes": 14,
        "successful_fresh_cores": 14,
        "root_open_cases": [
            "entry-hof-mirror-host-pre-once",
            "entry-legacy-host-pre-once",
            "entry-hof-legacy-host-pre-once",
        ],
        "acceptance_claimed": False,
        "release_ready": False,
    })
    observations = report.get("observations")
    need(type(observations) is list and len(observations) == 14, "diagnostic observation count differs")
    need(aggregate["entry_diagnostic_processes"] == 14
         and aggregate["entry_diagnostic_successful_fresh_cores"] == 14,
         "aggregate diagnostic count differs")
    for observation in observations:
        name = observation["name"]
        prefix = "pr16-generic-form-carry/" + name
        process(files, prefix, 0)
        need(b"mGBA[" not in files[prefix + ".stderr"], "diagnostic emulator warning")
        need(same(load(files[prefix + ".stdout"]), observation["result"]),
             "diagnostic aggregate/raw mismatch: " + name)
        need(observation["result"]["acceptance_claimed"] is False, "diagnostic promoted to acceptance")
    return report


def _validate_sources(root: Path, files: dict[str, bytes]) -> dict[str, Any]:
    bindings = load(files["pr16-generic-form-evidence/source-bindings.json"])
    snapshot = archive(files["pr16-generic-form-evidence/sources.zip"])
    need(set(bindings) == set(snapshot), "source snapshot/binding inventory differs")
    for name, wanted in bindings.items():
        need(identity(snapshot[name]) == wanted, "source snapshot digest differs: " + name)
    for name in SOURCE_BINDINGS:
        need(name in snapshot, "executed source missing from snapshot: " + name)
        need(read(root, name) == snapshot[name], "executed source changed since native run: " + name)
    return bindings


def build(root: Path = ROOT) -> dict[str, Any]:
    directory = Path(DIRECTORY) / str(RUN)
    metadata(load(read(root, directory / "actions.json")))
    raw = read(root, directory / "original.zip")
    need(identity(raw) == {"size": ARTIFACT_SIZE, "sha256": ARTIFACT_SHA256}, "original artifact differs")
    files = archive(raw)
    need(files["pr16-generic-form-evidence/tested-head.txt"].decode().strip() == HEAD, "tested HEAD differs")
    bindings = _validate_sources(root, files)
    process(files, "pr16-generic-form-carry/compile", 0)
    aggregate = load(files["pr16-generic-form-carry/result.json"])
    fields(aggregate, {
        "schema_version": 1,
        "status": "PASS",
        "scope": "PR16_P03_GENERIC_FORM_CARRY_PHYSICAL",
        "candidate": CANDIDATE,
        "failures": [],
        "diagnostic_failures": [],
        "guard_checks": list(GUARDS),
        "actual_new_processes": 2,
        "successful_fresh_cores": 5,
        "generic_form_carry_physical_accepted": True,
        "fixed_form_transition_physical_accepted": False,
        "full_p03_acceptance": False,
        "release_ready": False,
        "old_runs_relabelled": 0,
        "entry_diagnostic_status": "PASS_DIAGNOSTIC_ONLY",
    })
    need([item["name"] for item in aggregate["results"]] == list(CASES), "acceptance case inventory differs")
    cases = [_validate_case(files, aggregate, name) for name in CASES]
    diagnostics = _validate_diagnostics(files, aggregate)
    for guard in GUARDS:
        prefix = "pr16-generic-form-carry/guard-" + guard
        process(files, prefix, 1)
        need(files[prefix + ".stdout"] == b"", "guard stdout differs")
        need(files[prefix + ".stderr"] == b"P03 archive: host write after observation barrier\n",
             "guard failure differs: " + guard)
    picture_names = [name for name, value in files.items() if name.endswith(".ppm")]
    need(len(picture_names) == 44, "rendered witness count differs")
    for name in picture_names:
        picture = files[name]
        need(len(picture) == 115215 and picture.startswith(b"P6\n240 160\n255\n"),
             "rendered witness differs: " + name)
    return {
        "schema_version": 1,
        "status": "PASS_GENERIC_FORM_CARRY_ON_PARENT_PENDING_FIXED_AND_P08_TRANSFER",
        "condition_id": CONDITION,
        "candidate": CANDIDATE,
        "evidence": {
            "run_id": RUN,
            "tested_head": HEAD,
            "workflow": WORKFLOW,
            "job_id": JOB,
            "artifact_id": ARTIFACT,
            "artifact_name": ARTIFACT_NAME,
            "artifact_path": str(directory / "original.zip"),
            "artifact_size": ARTIFACT_SIZE,
            "artifact_sha256": ARTIFACT_SHA256,
            "source_snapshot_sha256": identity(files["pr16-generic-form-evidence/sources.zip"])["sha256"],
            "source_binding_count": len(bindings),
        },
        "accepted_scope": {
            "owner": "generic_form_change_service",
            "representative_species": [749, 900],
            "representative_route_ids": cases[0]["representative_route_ids"],
            "generic_owner_route_count": 61,
            "generic_owner_species_count": 10,
            "generic_owner_rows_sha256": cases[0]["generic_owner_rows_sha256"],
            "representative_native_acceptance": True,
            "all_61_rows_individually_executed": False,
            "menu_discovery": "input-only-native-menu-probe",
            "menu_page": 1,
            "menu_cursor": 1,
            "probe_count": 7,
            "pages_scanned": 2,
            "four_move_slots_preserved": True,
            "cancel_state_unchanged": True,
            "normal_save_and_fresh_continue": True,
        },
        "native_execution": {
            "acceptance_processes": 2,
            "acceptance_fresh_cores": 5,
            "diagnostic_processes": diagnostics["actual_new_processes"],
            "diagnostic_fresh_cores": diagnostics["successful_fresh_cores"],
            "diagnostics_are_acceptance": False,
            "cases": [
                {
                    "name": row["case"],
                    "result": row["result"],
                    "rounds": row["rounds"],
                    "fresh_cores": row["fresh_cores"],
                    "automatic_saves": row["automatic_saves"],
                    "manual_saves": row["manual_saves"],
                }
                for row in cases
            ],
            "write_guard_checks": list(GUARDS),
            "rendered_witnesses": len(picture_names),
        },
        "generic_form_carry_physical_accepted": True,
        "fixed_form_transition_physical_accepted": False,
        "full_p03_acceptance": False,
        "successor_transfer_complete": False,
        "clean_rom_regeneration_verified": False,
        "release_ready": False,
        "active_baseline_changed": False,
        "old_runs_relabelled": 0,
        "emulator_runs_by_this_verifier": 0,
    }


def fetch(root: Path = ROOT) -> None:
    def api(path: str) -> bytes:
        return subprocess.check_output(["gh", "api", "repos/" + REPO + "/" + path])

    run = load(api(f"actions/runs/{RUN}"))
    jobs_document = load(api(f"actions/runs/{RUN}/jobs?per_page=100"))
    artifact = load(api(f"actions/artifacts/{ARTIFACT}"))
    fields(artifact["workflow_run"], {"id": RUN, "head_sha": HEAD})
    need(artifact["digest"] == "sha256:" + ARTIFACT_SHA256, "artifact API digest differs")
    need(jobs_document["total_count"] == len(jobs_document["jobs"]) == 1, "job listing differs")
    job = jobs_document["jobs"][0]
    actions = {
        "artifact_id": artifact["id"],
        "artifact_name": artifact["name"],
        "conclusion": run["conclusion"],
        "head_branch": run["head_branch"],
        "head_sha": run["head_sha"],
        "jobs": [{
            "conclusion": job["conclusion"],
            "head_sha": job["head_sha"],
            "id": job["id"],
            "name": job["name"],
            "run_id": job["run_id"],
            "status": job["status"],
            "steps": [
                {key: step[key] for key in ("name", "number", "status", "conclusion")}
                for step in job["steps"]
            ],
        }],
        "path": run["path"],
        "run_attempt": run["run_attempt"],
        "run_id": run["id"],
        "sha256": ARTIFACT_SHA256,
        "size": artifact["size_in_bytes"],
        "status": run["status"],
    }
    metadata(actions)
    raw = api(f"actions/artifacts/{ARTIFACT}/zip")
    need(identity(raw) == {"size": ARTIFACT_SIZE, "sha256": ARTIFACT_SHA256}, "downloaded artifact differs")
    archive(raw)
    directory = root / DIRECTORY / str(RUN)
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in (("original.zip", raw), ("actions.json", stable(actions))):
        target = directory / name
        if target.exists():
            need(target.read_bytes() == value, "refuse original overwrite: " + str(target))
        else:
            target.write_bytes(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.fetch:
            fetch()
        value = build()
        path = ROOT / RECEIPT
        if args.write:
            if path.exists():
                need(same(load(path.read_bytes()), value), "refuse receipt replacement")
            else:
                path.write_bytes(stable(value))
        else:
            need(same(load(path.read_bytes()), value), "stored generic FORM receipt differs")
        print(json.dumps({
            "status": "PASS",
            "condition_id": CONDITION,
            "candidate_sha256": CANDIDATE["sha256"],
            "original_run_id": RUN,
            "new_emulator_runs": 0,
            "full_p03_acceptance": False,
            "release_ready": False,
        }, ensure_ascii=False))
        return 0
    except (CheckpointError, KeyError, TypeError, OSError, json.JSONDecodeError,
            zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
