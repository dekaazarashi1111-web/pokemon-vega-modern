#!/usr/bin/env python3
"""P01 runner復元: 衝突する固定Wiki reportの現在版・旧版を両方保全する。

既存restoreのhash検査・symlink拒否・衝突拒否は変更しない。--forceは禁止。
対象は実測済みのGit blob 1件に固定し、復元中だけ同じfilesystem内で退避する。
ROM/save/元ZIPは上書きせず、reportの旧版も.localへ保持する。
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.github_private_environment import PrivateEnvironmentError, _destination, _load_config, restore_archive, restore_links

REPORT = "reports/generated/stage61_wiki.json"
REPORT_BLOB = "ec3c2e823bf422dcd72ec19951be83128c83651a"


def blob_identity(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


@contextmanager
def preserve_report(root: Path, expected_blob: str = REPORT_BLOB):
    """yield中の失敗でも元reportを復帰。退避先は予測可能な既存pathを使わない。"""
    target = _destination(root, REPORT)
    if target.is_symlink() or not target.is_file():
        raise PrivateEnvironmentError("P01_REPORT_NOT_REGULAR")
    before = target.read_bytes()
    if blob_identity(before) != expected_blob:
        raise PrivateEnvironmentError("P01_REPORT_HEAD_IDENTITY_MISMATCH")
    private = root / ".local"
    if private.resolve() != private.absolute():
        raise PrivateEnvironmentError("P01_BACKUP_SYMLINK_FORBIDDEN")
    private.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="p01-snapshot-report-", dir=private))
    current = directory / "current.json"
    archived = directory / "archived.json"
    os.replace(target, current)
    evidence = {"current_blob": expected_blob, "current_sha256": hashlib.sha256(before).hexdigest(),
                "archived_sha256": None, "current_preserved": False}
    try:
        yield evidence
    finally:
        # 親symlink等の不正を検出した場合、元byteはcurrent.jsonに保存したままfail closed。
        if _destination(root, REPORT) != target or target.parent.resolve() != target.parent.absolute():
            raise PrivateEnvironmentError("P01_REPORT_PARENT_CHANGED")
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_file():
                raise PrivateEnvironmentError("P01_RESTORED_REPORT_NOT_REGULAR")
            evidence["archived_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            os.replace(target, archived)
        if current.is_symlink() or current.read_bytes() != before:
            raise PrivateEnvironmentError("P01_CURRENT_REPORT_BACKUP_CHANGED")
        os.replace(current, target)
        if target.read_bytes() != before:
            raise PrivateEnvironmentError("P01_CURRENT_REPORT_RESTORE_MISMATCH")
        evidence["current_preserved"] = True


def restore(root: Path, archive_dir: Path) -> dict:
    config = _load_config(root / "config/github_private_environment.json")
    tracked = subprocess.check_output(["git", "ls-files", "-s", "--", REPORT], cwd=root, text=True).split()
    if len(tracked) != 4 or tracked[0] != "100644" or tracked[1] != REPORT_BLOB or tracked[2] != "0":
        raise PrivateEnvironmentError("P01_TRACKED_REPORT_PIN_MISMATCH")
    with preserve_report(root) as report:
        results = [restore_archive(root, archive_dir / row["name"], row, False) for row in config["archives"]]
        links = restore_links(root, config, False)
    if not report["current_preserved"] or report["archived_sha256"] is None:
        raise PrivateEnvironmentError("P01_TWO_REPORT_VERSIONS_NOT_PRESERVED")
    return {"schema_version": 1, "status": "PASS", "archives": results, "input_links": links,
            "wiki_report": report, "force_used": False, "original_archives_changed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = restore(ROOT, args.archive_dir)
    except Exception as exc:
        # 本文・private path・入力値は公開しない。既知のtracked衝突pathだけを限定通知。
        result = {"schema_version": 1, "status": "FAIL", "exception_type": type(exc).__name__}
        message = str(exc)
        prefix = "既存fileと衝突しました: "
        if message.startswith(prefix):
            try:
                relative = Path(message[len(prefix):]).relative_to(ROOT).as_posix()
                listed = subprocess.check_output(["git", "ls-files", "--", relative], cwd=ROOT, text=True).strip()
                if listed == relative and relative.startswith("reports/generated/") and relative.endswith(".json"):
                    result["tracked_report_collision"] = relative
            except (ValueError, OSError, subprocess.SubprocessError):
                pass
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
