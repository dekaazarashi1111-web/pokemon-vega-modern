#!/usr/bin/env python3
"""Git管理へ統合した受領資料が受領時点から変化していないか検証する。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_ROOT = ROOT / "audit_seed"
DESIGN_PACKAGES = (
    {
        "label": "設計V1（来歴）",
        "root": ROOT / "design" / "imported" / "VEGA_CFRU_DPE_統合設計",
        "status_key": "package_status",
        "status": "design_only_not_playable_patch",
        "size_key": "size",
        "sha_manifest": False,
    },
    {
        "label": "設計V2（二地方・現行）",
        "root": (
            ROOT
            / "design"
            / "imported"
            / "VEGA_CFRU_DPE_統合設計_V2_二地方生態版"
        ),
        "status_key": "status",
        "status": "design-specification-only",
        "version": "V2",
        "size_key": "size_bytes",
        "sha_manifest": True,
    },
)


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


def safe_relative(raw_path: str, label: str, errors: list[str]) -> Path | None:
    relative = Path(raw_path)
    if (
        not raw_path
        or relative == Path(".")
        or relative.is_absolute()
        or ".." in relative.parts
        or "\\" in raw_path
    ):
        errors.append(f"{label}に安全でないpath: {raw_path}")
        return None
    return relative


def read_sha_manifest(path: Path, label: str, errors: list[str]) -> dict[Path, str]:
    records: dict[Path, str] = {}
    if not path.is_file():
        errors.append(f"{label}がありません: {path.relative_to(ROOT)}")
        return records
    for lineno, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            expected_hash, raw_path = line.split(maxsplit=1)
        except ValueError:
            errors.append(f"{path.relative_to(ROOT)}:{lineno}: 書式不正")
            continue
        relative = safe_relative(raw_path.removeprefix("*"), label, errors)
        if relative is None:
            continue
        if relative in records:
            errors.append(f"{label}でpath重複: {relative}")
            continue
        records[relative] = expected_hash.lower()
    return records


def verify_design(package: dict[str, Any]) -> tuple[list[str], int]:
    errors: list[str] = []
    design_root: Path = package["root"]
    label: str = package["label"]
    manifest_path = design_root / "manifest.json"
    if not manifest_path.is_file():
        return [f"{label}のmanifestがありません: {manifest_path.relative_to(ROOT)}"], 0

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{label}のmanifestを読めません: {exc}"], 0

    if manifest.get(package["status_key"]) != package["status"]:
        errors.append(f"{label}のstatusが想定外です")
    if package.get("version") and manifest.get("version") != package["version"]:
        errors.append(f"{label}のversionが想定外です")

    expected_paths: set[Path] = set()
    records = manifest.get("files")
    if not isinstance(records, list):
        return [*errors, f"{label}のfilesが配列ではありません"], 0
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{label}のfiles[{index}]がobjectではありません")
            continue
        relative = safe_relative(str(record.get("path", "")), label, errors)
        if relative is None:
            continue
        if relative in expected_paths:
            errors.append(f"{label}のmanifestでpath重複: {relative}")
            continue
        expected_paths.add(relative)
        target = design_root / relative
        if not target.is_file():
            errors.append(f"{label}ファイル欠落: {relative}")
            continue
        actual_size = target.stat().st_size
        expected_size = record.get(package["size_key"])
        if actual_size != expected_size:
            errors.append(
                f"{label}size不一致: {relative} "
                f"expected={expected_size} actual={actual_size}"
            )
        expected_hash = str(record.get("sha256", "")).lower()
        if sha256(target) != expected_hash:
            errors.append(f"{label}hash不一致: {relative}")

    actual_paths = {
        path.relative_to(design_root)
        for path in design_root.rglob("*")
        if path.is_file()
        and path != manifest_path
        and (not package["sha_manifest"] or path.name != "MANIFEST.sha256")
    }
    missing_records = actual_paths - expected_paths
    if missing_records:
        errors.append(
            f"{label}manifest外ファイル: " + ", ".join(map(str, sorted(missing_records)))
        )
    absent_files = expected_paths - actual_paths
    if absent_files:
        errors.append(
            f"{label}manifest対象欠落: " + ", ".join(map(str, sorted(absent_files)))
        )

    if package["sha_manifest"]:
        sha_records = read_sha_manifest(
            design_root / "MANIFEST.sha256", f"{label}のMANIFEST.sha256", errors
        )
        json_records = {
            Path(record["path"]): str(record["sha256"]).lower()
            for record in records
            if isinstance(record, dict) and record.get("path") and record.get("sha256")
        }
        if sha_records != json_records:
            errors.append(f"{label}のJSON manifestとMANIFEST.sha256が不一致です")

    return errors, len(expected_paths)


def main() -> int:
    errors = verify_audit()
    design_counts: list[int] = []
    for package in DESIGN_PACKAGES:
        package_errors, count = verify_design(package)
        errors.extend(package_errors)
        design_counts.append(count)
    if errors:
        print("受領資料の整合性検査: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "受領資料の整合性検査: PASS"
        f"（監査15件、設計V1 {design_counts[0]}件、設計V2 {design_counts[1]}件）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
