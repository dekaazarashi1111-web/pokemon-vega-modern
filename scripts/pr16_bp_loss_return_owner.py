#!/usr/bin/env python3
"""BP敗北後のWhiteOut/field-return所有者を固定sourceから読取監査する。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Iterable

SCHEMA_VERSION = 1
TASK = "USER-20260913-BP-LOSS-RETURN-OWNER"
SOURCE_ROOT = Path("vendor/upstream/CFRU-JP")
TRACKED_BUILD = Path("scripts/build_battle_core.py")
NEEDLES = (
    "CB2_WhiteOut",
    "CB2_ReturnToField",
    "EndOfBattleThings",
    "EndBattleFlagClear",
    "BATTLE_TYPE_FRONTIER",
    "BATTLE_TYPE_BATTLE_TOWER",
    "VegaBattlePolicyEnd",
)
REQUIRED = (
    "CB2_WhiteOut",
    "CB2_ReturnToField",
    "EndOfBattleThings",
    "EndBattleFlagClear",
    "BATTLE_TYPE_FRONTIER",
    "VegaBattlePolicyEnd",
)
TEXT_SUFFIXES = {".c", ".h", ".py"}
CONTEXT = 24
MAX_MATCHES_PER_NEEDLE = 80
MAX_FILE_SIZE = 2_000_000


class OwnerAuditError(ValueError):
    """固定source、監査範囲、または出力が契約外。"""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise OwnerAuditError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def identity(raw: bytes) -> dict[str, object]:
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def safe_path(root: Path, logical: Path) -> Path:
    need(not logical.is_absolute() and ".." not in logical.parts, f"unsafe path: {logical}")
    root = root.resolve()
    path = (root / logical).resolve()
    need(path == root or root in path.parents, f"path escapes root: {logical}")
    for item in (path, *path.parents):
        if item == root.parent:
            break
        need(not item.is_symlink(), f"symlink rejected: {logical}")
    return path


def source_files(root: Path) -> list[Path]:
    base = safe_path(root, SOURCE_ROOT)
    need(base.is_dir(), f"missing fixed CFRU source: {SOURCE_ROOT}")
    rows: list[Path] = []
    for path in base.rglob("*"):
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in TEXT_SUFFIXES:
            rows.append(path)
    tracked = safe_path(root, TRACKED_BUILD)
    need(tracked.is_file() and not tracked.is_symlink(), f"missing tracked build source: {TRACKED_BUILD}")
    rows.append(tracked)
    rows.sort(key=lambda p: p.relative_to(root.resolve()).as_posix())
    need(rows, "no audit source files")
    return rows


def read_text(path: Path) -> tuple[bytes, list[str]]:
    raw = path.read_bytes()
    need(len(raw) <= MAX_FILE_SIZE and b"\0" not in raw, f"non-text or oversized source: {path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("shift_jis")
    return raw, text.splitlines()


def source_identity(root: Path) -> dict[str, object]:
    base = safe_path(root, SOURCE_ROOT)
    result: dict[str, object] = {"path": SOURCE_ROOT.as_posix()}
    git_dir = base / ".git"
    if git_dir.exists():
        for label, args in (
            ("commit", ("rev-parse", "HEAD")),
            ("tree", ("rev-parse", "HEAD^{tree}")),
            ("status", ("status", "--porcelain")),
        ):
            run = subprocess.run(
                ["git", "-C", str(base), *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            need(run.returncode == 0, f"fixed source git {label} failed: {run.stderr.strip()}")
            value = run.stdout.strip()
            if label == "status":
                need(value == "", "fixed CFRU source worktree is dirty")
            else:
                result[label] = value
    return result


def matches(root: Path, paths: Iterable[Path]) -> tuple[dict[str, list[dict[str, object]]], dict[str, dict[str, object]]]:
    root = root.resolve()
    found = {needle: [] for needle in NEEDLES}
    files: dict[str, dict[str, object]] = {}
    for path in paths:
        raw, lines = read_text(path)
        rel = path.relative_to(root).as_posix()
        touched = False
        for line_no, line in enumerate(lines, 1):
            for needle in NEEDLES:
                if needle not in line:
                    continue
                need(len(found[needle]) < MAX_MATCHES_PER_NEEDLE, f"too many matches for {needle}")
                start = max(1, line_no - CONTEXT)
                end = min(len(lines), line_no + CONTEXT)
                context_lines = lines[start - 1:end]
                context_text = "\n".join(context_lines) + "\n"
                found[needle].append(
                    {
                        "path": rel,
                        "line": line_no,
                        "text": line.strip(),
                        "context_start": start,
                        "context_end": end,
                        "context_sha256": hashlib.sha256(context_text.encode("utf-8")).hexdigest(),
                        "context": context_text,
                    }
                )
                touched = True
        if touched:
            files[rel] = identity(raw)
    for needle in REQUIRED:
        need(found[needle], f"required owner token absent: {needle}")
    return found, files


def classify(found: dict[str, list[dict[str, object]]]) -> dict[str, object]:
    whiteout_paths = sorted({str(row["path"]) for row in found["CB2_WhiteOut"]})
    return_paths = sorted({str(row["path"]) for row in found["CB2_ReturnToField"]})
    end_paths = sorted({str(row["path"]) for key in ("EndOfBattleThings", "EndBattleFlagClear", "VegaBattlePolicyEnd") for row in found[key]})
    overlap = sorted(set(whiteout_paths) & set(return_paths))
    return {
        "whiteout_owner_paths": whiteout_paths,
        "field_return_owner_paths": return_paths,
        "end_lifecycle_paths": end_paths,
        "whiteout_and_return_overlap_paths": overlap,
        "owner_resolved": bool(overlap),
        "candidate_rom_changed": False,
        "new_emulator_processes": 0,
        "accepted_native_cases_replayed": 0,
    }


def render_excerpts(found: dict[str, list[dict[str, object]]]) -> str:
    blocks: list[str] = []
    seen: set[tuple[str, int, int, str]] = set()
    for needle in NEEDLES:
        blocks.append(f"## {needle}\n")
        for row in found[needle]:
            key = (str(row["path"]), int(row["context_start"]), int(row["context_end"]), str(row["context_sha256"]))
            if key in seen:
                blocks.append(
                    f"- duplicate-context: {row['path']}:{row['line']} sha256={row['context_sha256']}\n"
                )
                continue
            seen.add(key)
            blocks.append(
                f"### {row['path']}:{row['line']} lines {row['context_start']}-{row['context_end']} sha256={row['context_sha256']}\n"
            )
            start = int(row["context_start"])
            for offset, text in enumerate(str(row["context"]).splitlines(), start):
                blocks.append(f"{offset:6d}: {text}\n")
    return "".join(blocks)


def audit(root: Path) -> tuple[dict[str, object], str]:
    root = root.resolve()
    found, files = matches(root, source_files(root))
    report: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "classification": "SOURCE_ONLY_OWNER_AUDIT_NOT_NATIVE_ACCEPTANCE",
        "fixed_source": source_identity(root),
        "needles": {key: len(rows) for key, rows in found.items()},
        "matched_files": files,
        "matches": found,
        "sumary": classify(found),
        "release_ready": False,
        "native_bp_earning_accepted": False,
    }
    return report, render_excerpts(found)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report, excerpts = audit(args.root)
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    need(not out.is_symlink(), "output directory symlink rejected")
    (out / "owner-report.json").write_bytes(stable(report))
    (out / "owner-excerpts.txt").write_text(excerpts, encoding="utf-8", newline="\n")
    print(stable({"status": "PASS", "summary": report["summary"], "needles": report["needles"]}).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
