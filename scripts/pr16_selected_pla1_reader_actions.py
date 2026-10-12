#!/usr/bin/env python3
"""新PLA1 readerのみ測定。既受入の全owner/native/音声/生成試験は再走しない。"""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import traceback
import unittest
import zipfile

import pr16_selected_pla1_reader as m
import pr16_wiki_r0_reconcile_actions as a

ROOT = Path(__file__).resolve().parents[1]
START = "f031d5cdb5188c15a49d8a21a45b6d0ed2512276"
BRANCH = "codex/modernization-followup-20260908"
TASK = "USER-20261012-SELECTED-PLA1-READER"
STATE = "content/modernization/pr16_wiki_first_execution_plan.json"
REPORT = "content/modernization/pr16_selected_pla1_reader_checkpoint.json"
WORK = ROOT / ".local/pr16-selected-pla1-reader"
PUBLIC = WORK / "public"
PHASE = "preflight"
COUNTS = {"rom_reconstructions_started": 0, "new_reader_profiles_completed": 0,
          "accepted_test_reruns": 0, "accepted_measurement_reruns": 0, "native_processes": 0}
CODE = {"scripts/pr16_selected_pla1_reader.py", "scripts/pr16_selected_pla1_reader_actions.py",
        "tests/test_pr16_selected_pla1_reader.py", ".github/workflows/pr16-selected-pla1-reader.yml"}
ENGINES = {"scripts/pr16_dex_hof_runtime_sprite.py": "7eb841b9a06ebedf2f8307ee5c8ff1135aeb355b",
           "scripts/pr16_dex_hof_lifetime_root.py": "83339dbb39cdba0cc21c535c66ceb9ce243c3f22"}


def read(name):
    p = ROOT / name
    m.need(p.is_file() and not p.is_symlink(), "通常入力file")
    return p.read_bytes()


def load(name):
    return json.loads(read(name))


def write(name, value):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / name).write_bytes(m.encode(value) if isinstance(value, dict) else value)


def blob(data):
    import hashlib
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def aligned(checkpoint):
    spec = checkpoint["artifacts"]["aligned_data"]
    meta = a.fetch("actions/artifacts/" + str(spec["id"]))
    m.need(not meta["expired"] and all(meta[k] == spec[k] for k in ("id", "name", "size_in_bytes", "digest"))
           and meta["workflow_run"]["id"] == 35748601580, "保存ARM artifact metadata")
    raw = a.fetch("actions/artifacts/" + str(spec["id"]) + "/zip", binary=True)
    m.need(m.identity(raw) == {"size": spec["size_in_bytes"], "sha256": spec["digest"][7:]}, "保存ARM ZIP全hash")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        m.need(len(names) == len(set(names)) == 7 and set(names) == set(checkpoint["data_files"]), "保存ARM閉7member")
        result = {}
        for info in z.infolist():
            p = PurePosixPath(info.filename)
            m.need(not p.is_absolute() and ".." not in p.parts and not info.is_dir()
                   and (info.external_attr >> 16) & 0o170000 != 0o120000 and info.file_size < 100000, "通常有限member")
            data = z.read(info)
            m.need(m.identity(data) == checkpoint["data_files"][info.filename], "保存ARM member hash")
            result[info.filename] = data
    return result, {"artifact": spec, "member_identities": checkpoint["data_files"], "arm_recompiles": 0, "archive_regenerations": 0}


def context(paths):
    target = PUBLIC / "scoped-context.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(paths):
            data = read(path)
            data.decode("utf-8")
            m.need(len(data) < 1000000 and b"\0" not in data and a.git("show", "HEAD:" + path) == data, "限定tracked text原本")
            info = zipfile.ZipInfo(path, (2026, 10, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)


def run():
    global PHASE
    m.need(os.environ.get("GITHUB_REPOSITORY") == a.REPO
           and os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH
           and os.environ.get("GITHUB_RUN_ATTEMPT") == "1", "固定branch初回のみ")
    head = a.git("rev-parse", "HEAD").decode().strip()
    m.need(head == os.environ["GITHUB_SHA"] and not WORK.exists() and not (ROOT / REPORT).exists(), "event HEAD/未測定scope")
    m.need(not a.git("status", "--porcelain", "--untracked-files=no").strip(), "tracked clean")
    m.need(set(a.git("diff", "--name-only", START, head).decode().splitlines()) == CODE, "新4fileのみ")
    nested = [p + "/AGENTS.md" for p in ("scripts", "tests", "docs", "design", "content", "content/modernization", ".github", ".github/workflows")]
    m.need(not a.git("ls-files", "--", *nested).strip(), "追加AGENTS確認")
    state = load(STATE)
    m.need(state["next_action"]["id"] == "SAVE_CAPACITY_SELECTED_PLA1_AND_IPS_ACTUAL_READER", "固定next")
    lane = state["owner_execution_plan"]["technical_lanes"]["save_capacity"]
    m.need([lane[k] for k in ("classified", "unclassified", "selected_unknown_origins", "donor_safe_bytes")] == [789, 85, 6, 0], "正式値保全")
    for path, expected in ENGINES.items():
        m.need(blob(read(path)) == expected, "受入済みCPU source不変")
    PUBLIC.mkdir(parents=True)
    write("starting-head-checks.json", a.live(head))
    protected = {STATE, "CHATGPT_RESUME.md", "docs/PR16_FOREST_WALLPAPER_ASSET_JA.md", "AGENTS.md",
                 "content/modernization/pr16_selected_compressed_asset_checkpoint.json",
                 "content/modernization/pr16_selected_compressed_asset_evidence/compressed-asset.json",
                 "content/modernization/pr16_selected_compressed_asset_evidence/actions-completion.json",
                 "content/modernization/pr16_selected_asset_provenance_evidence/provenance.json",
                 "content/modernization/pr16_learnset_supply_checkpoint.json",
                 "content/modernization/pr16_learnset_supply_alignment_checkpoint.json",
                 "content/modernization/pr16_dex_hof_generation_writer_checkpoint.json",
                 "src/modernization/pr16_learnset_supply.c", "src/modernization/pr16_learnset_supply.h",
                 "src/modernization/pr16_learnset_runtime.h", "src/modernization/pr16_learnset_owner.h", *ENGINES}
    before = {p: (m.identity(read(p)), (ROOT / p).stat().st_mtime_ns) for p in protected}
    context(protected | CODE)
    PHASE = "new-boundary-tests"
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_pr16_selected_pla1_reader.py"))
    write("reader-tests.txt", stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun == 36 and not tests.skipped, "新36境界試験")
    graph = subprocess.run(["python3", "-B", "scripts/validate_task_graph.py"], cwd=ROOT, capture_output=True, check=True)
    write("task-graph.txt", graph.stdout)
    PHASE = "saved-source-and-arm"
    original = load("content/modernization/pr16_learnset_supply_checkpoint.json")
    for path in ("src/modernization/pr16_learnset_supply.c", "src/modernization/pr16_learnset_supply.h"):
        m.need(m.identity(read(path)) == original["verification"]["code_bindings"][path], "consumer C原本")
    files, receipt = aligned(load("content/modernization/pr16_learnset_supply_alignment_checkpoint.json"))
    write("saved-arm-reuse.json", receipt)
    PHASE = "one-new-reader-scope-reconstruction"
    import pr16_dex_hof_capacity_actions as builder
    builder.OUT = WORK / "candidate"
    builder.OUT.mkdir()
    COUNTS["rom_reconstructions_started"] = 1
    write("attempt.json", COUNTS)
    with (WORK / "private-reconstruction.log").open("w") as private, contextlib.redirect_stdout(private), contextlib.redirect_stderr(private):
        raw, checkpoint = builder.reconstruct()
    m.need(checkpoint["candidate"] == m.CANDIDATE, "現候補全SHA")
    PHASE = "actual-conditional-pla1-reader"
    proof = m.prove(raw, files["archive-image.bin"], files["supply.bin"])
    COUNTS["new_reader_profiles_completed"] = len(proof["profiles"])
    proof.update(source_head=head, actions_run_id=int(os.environ["GITHUB_RUN_ID"]),
                 actions_completion_confirmed=False, source_bindings={p: m.identity(read(p)) for p in sorted(CODE | set(ENGINES))},
                 preserved_inputs={p: value[0] for p, value in before.items()}, **COUNTS)
    write("pla1-reader.json", proof)
    write("attempt.json", COUNTS)
    m.need(before == {p: (m.identity(read(p)), (ROOT / p).stat().st_mtime_ns) for p in protected}
           and not a.git("diff", "--name-only").strip(), "全原本byte/mtime・tracked不変")
    summary = {"status": "MEASURED_PLA1_CONDITIONAL_READER_RECEIPT_PENDING", "source_head": head,
               "actions_run_id": int(os.environ["GITHUB_RUN_ID"]), "new_unit_tests": tests.testsRun,
               "target": m.TARGET, "owner": m.OWNER, "family": m.FAMILY,
               "roles": [r["role"] for r in proof["target_roles"]],
               "profiles": [{k: row[k] for k in ("capacity", "returned", "output_count", "instruction_count")} for row in proof["profiles"]],
               "formal_classified": 789, "formal_unclassified": 85, "selected_unknown_origins": 6,
               "donor_safe_bytes": 0, "other_two_targets_reader_proven": False, **COUNTS}
    write("result.json", summary)
    print("PLA1_SUMMARY=" + json.dumps(summary, sort_keys=True, ensure_ascii=False))
    print("RESULT=DONE TASK=" + TASK + " VERIFY=PASS COMMIT=-")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        write("failure.json", {"status": "NOT_ACCEPTED", "phase": PHASE, "exception_type": type(exc).__name__,
                               "frames": [{"file": Path(f.filename).name, "line": f.lineno}
                                          for f in traceback.extract_tb(exc.__traceback__) if "/scripts/" in f.filename], **COUNTS})
        print("RESULT=BLOCKED TASK=" + TASK + " VERIFY=FAIL TYPE=" + type(exc).__name__)
        sys.exit(1)
