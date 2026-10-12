#!/usr/bin/env python3
"""選定IPS/DPE新規tracked textに追加private違反が無いことだけを正式guardとの差分で検査。

全indexに残存する歴史的違反を「guard成功」と書き換えない。
ROM/Saveの復元・測定・native・旧受入試験は一切実行しない。
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

import guard_private_files as private

ROOT = Path(__file__).resolve().parents[1]
BASE = "6acbf1d863c1527849475eb6002ff3ad613991e4"
BRANCH = "codex/modernization-followup-20260908"
WORK = ROOT / ".local/pr16-ips-dpe-private-guard"
PUBLIC = WORK / "public"
EXPECTED = frozenset({
    ".github/workflows/pr16-ips-dpe-boundary.yml",
    ".github/workflows/pr16-ips-dpe-private-guard.yml",
    "CHATGPT_RESUME.md",
    "content/modernization/pr16_selected_ips_dpe_frontier_checkpoint.json",
    "content/modernization/pr16_selected_ips_dpe_frontier_evidence/actions-completion.json",
    "content/modernization/pr16_selected_ips_dpe_frontier_evidence/ci-context.json",
    "content/modernization/pr16_selected_ips_dpe_frontier_evidence/dpe-source-chain.json",
    "content/modernization/pr16_wiki_first_execution_plan.json",
    "design/run_log.md",
    "design/version_log.md",
    "docs/PR16_FOREST_WALLPAPER_ASSET_JA.md",
    "scripts/pr16_selected_ips_dpe_frontier.py",
    "scripts/pr16_ips_dpe_private_guard.py",
    "tests/test_pr16_selected_ips_dpe_frontier.py",
    "tests/test_pr16_ips_dpe_private_guard.py",
})
TEXT_SUFFIXES = {".md", ".json", ".py", ".yml"}


def need(value, message: str) -> None:
    if not value:
        raise ValueError(message)


def git(*args: str, env=None, check=True) -> bytes:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, env=env, check=False)
    if check:
        need(proc.returncode == 0, "git subcommand failed: " + args[0])
    return proc.stdout if proc.returncode == 0 else b""


def safe(name: str) -> bool:
    p = PurePosixPath(name)
    return (not p.is_absolute() and ".." not in p.parts and "\\" not in name
            and p.suffix in TEXT_SUFFIXES
            and p.suffix.lower() not in private.BLOCKED_SUFFIXES
            and not any(name == x or name.startswith(x + "/") for x in private.BLOCKED_PARTS))


def added_absolute_paths(before: bytes, after: bytes) -> Counter:
    """行番号移動は無視し、危険な新しい実literal行だけを数える。"""
    def flagged(raw: bytes):
        lines = raw.decode("utf-8").splitlines()
        return Counter(lines[index - 1] for index in private.document_user_path_lines(raw))
    return flagged(after) - flagged(before)


def changed() -> tuple[list[str], list[dict]]:
    files = git("diff", "--name-only", "-z", BASE, "HEAD").decode("utf-8").strip("\0").split("\0")
    need(set(files) == EXPECTED and len(files) == len(EXPECTED), "changed paths differ from reviewed scope")
    proof = []
    for path in sorted(files):
        need(safe(path), "blocked path/suffix")
        tree = git("ls-tree", "HEAD", "--", path).decode().split()
        need(len(tree) == 4 and tree[0] in ("100644", "100755") and tree[1] == "blob"
             and tree[3] == path, "nonregular or mismatched tree entry")
        after = git("show", "HEAD:" + path)
        before = git("show", BASE + ":" + path, check=False)
        need(b"\0" not in after and len(after) < 8_000_000, "tracked binary/oversized text")
        after.decode("utf-8")
        if Path(path).suffix in private.DOCUMENT_SUFFIXES:
            need(not added_absolute_paths(before, after), "new machine-specific user path")
        if Path(path).suffix == ".zip":
            need(not private.blocked_zip_members(after), "ZIP with blocked private member")
        proof.append(dict(path=path,old_sha256=hashlib.sha256(before).hexdigest() if before else None,
                          new_sha256=hashlib.sha256(after).hexdigest(),new_byte_size=len(after),
                          new_absolute_user_path_lines=0,blocked_private_suffix=False))
    return sorted(files), proof


def full_index_guard(revision: str) -> dict:
    """同一guardを独立indexで旧ref/HEAD両方に実行。出力生pathを公開しない。"""
    with tempfile.TemporaryDirectory(dir=WORK) as name:
        env = dict(os.environ)
        env["GIT_INDEX_FILE"] = str(Path(name) / "guard.index")
        git("read-tree", revision, env=env)
        proc = subprocess.run([sys.executable, "-B", "scripts/guard_private_files.py"],
                              cwd=ROOT, env=env, capture_output=True, check=False)
    need(proc.returncode in (0, 1), "unexpected full guard error code")
    return dict(exit_code=proc.returncode, passed=proc.returncode == 0,
                stdout_sha256=hashlib.sha256(proc.stdout).hexdigest(),
                stderr_sha256=hashlib.sha256(proc.stderr).hexdigest(),
                raw_stdout_or_stderr_published=False)


def main() -> None:
    need(os.getenv("GITHUB_REPOSITORY") == "dekaazarashi1111-web/pokemon-vega-modern", "repository")
    need(os.getenv("GITHUB_REF") == "refs/heads/" + BRANCH, "branch")
    need(os.getenv("GITHUB_RUN_ATTEMPT") == "1", "no duplicate retry")
    need(not WORK.exists() and not git("status", "--porcelain", "--untracked-files=no").strip(), "workspace clean")
    head = git("rev-parse", "HEAD").decode().strip()
    need(head == os.environ.get("GITHUB_SHA") and head != BASE, "source head")
    PUBLIC.mkdir(parents=True)
    names, details = changed()
    before = full_index_guard(BASE)
    after = full_index_guard("HEAD")
    need(before["exit_code"] == 0 or after["exit_code"] == 0 or
         (before["exit_code"] == after["exit_code"] == 1), "historical full index failure regressed")
    result = dict(schema_version=1,task="USER-20261012-IPS-DPE-PRIVATE-DELTA-GUARD",
                  status="PASS_NEW_TRACKED_TEXT_PRIVATE_DELTA_ONLY",
                  base=BASE,source_head=head,compared_changed_paths=len(names),
                  changed_text=details,added_private_violations=0,
                  full_index_before=before,full_index_after=after,
                  full_index_green_claimed=after["passed"],
                  historical_full_index_failure_retained=not after["passed"],
                  accepted_test_reruns=0,old_native_reruns=0,rom_reconstructions=0,
                  no_private_original_content_published=True)
    target = PUBLIC / "result.json"
    target.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    need(json.loads(target.read_text(encoding="utf-8")) == result, "public proof round-trip")
    print("NEW_PRIVATE_DELTA_VIOLATIONS=0")
    print("BASE_FULL_GUARD_EXIT=" + str(before["exit_code"]))
    print("HEAD_FULL_GUARD_EXIT=" + str(after["exit_code"]))
    print("RESULT=DONE TASK=USER-20261012-IPS-DPE-PRIVATE-DELTA-GUARD VERIFY=PASS COMMIT=-")


if __name__ == "__main__":
    main()
