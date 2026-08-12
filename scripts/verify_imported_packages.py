#!/usr/bin/env python3
"""Git管理へ統合した受領資料が受領時点から変化していないか検証する。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_ROOT = ROOT / "audit_seed"
DESIGN_ROOT = ROOT / "design" / "imported" / "VEGA_CFRU_DPE_統合設計"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_audit() -> list[str]:
    errors: list[str] = []
    manifest = AUDIT_ROOT / "MANIFEST.sha256"
    if not manifest.is_file():
        return [f"監査manifestがありません: {manifest.relative_to(ROOT)}"]

    expected_paths: set[Path] = set()
    for lineno, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            expected_hash, raw_path = line.split(maxsplit=1)
        except ValueError:
            errors.append(f"{manifest.relative_to(ROOT)}:{lineno}: 書式不正")
            continue
        relative = Path(raw_path.removeprefix("./"))
        expected_paths.add(relative)
        target = AUDIT_ROOT / relative
        if not target.is_file():
            errors.append(f"監査ファイル欠落: {relative}")
        elif sha256(target) != expected_hash.lower():
            errors.append(f"監査hash不一致: {relative}")

    actual_paths = {
        path.relative_to(AUDIT_ROOT)
        for path in AUDIT_ROOT.rglob("*")
        if path.is_file()
        and path != manifest
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    }
    extras = actual_paths - expected_paths
    if extras:
        errors.append("監査manifest外ファイル: " + ", ".join(map(str, sorted(extras))))
    return errors


def verify_design() -> list[str]:
    errors: list[str] = []
    manifest_path = DESIGN_ROOT / "manifest.json"
    if not manifest_path.is_file():
        return [f"設計manifestがありません: {manifest_path.relative_to(ROOT)}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"設計manifestを読めません: {exc}"]

    if manifest.get("package_status") != "design_only_not_playable_patch":
        errors.append("設計package_statusが想定外です")

    expected_paths: set[Path] = set()
    for record in manifest.get("files", []):
        relative = Path(record["path"])
        expected_paths.add(relative)
        target = DESIGN_ROOT / relative
        if not target.is_file():
            errors.append(f"設計ファイル欠落: {relative}")
            continue
        actual_size = target.stat().st_size
        if actual_size != record["size"]:
            errors.append(
                f"設計size不一致: {relative} expected={record['size']} actual={actual_size}"
            )
        if sha256(target) != record["sha256"].lower():
            errors.append(f"設計hash不一致: {relative}")

    actual_paths = {
        path.relative_to(DESIGN_ROOT)
        for path in DESIGN_ROOT.rglob("*")
        if path.is_file() and path != manifest_path
    }
    missing_records = actual_paths - expected_paths
    if missing_records:
        errors.append("設計manifest外ファイル: " + ", ".join(map(str, sorted(missing_records))))
    return errors


def main() -> int:
    errors = [*verify_audit(), *verify_design()]
    if errors:
        print("受領資料の整合性検査: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("受領資料の整合性検査: PASS（監査15件、設計35件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
